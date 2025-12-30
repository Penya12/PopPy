from collections.abc import Generator

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, RootTransaction, event
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer

import poppy.db.session as db_session_module
from alembic import command
from poppy.api.app import app
from poppy.services.utils import ALEMBIC_INI_PATH

# If your project uses postgresql+psycopg, keep it consistent:
DRIVER_PREFIX = "postgresql+psycopg"
EXPOSED_PORT = 5432


def get_postgres_url_for_tests(container: PostgresContainer) -> str:
    host = container.get_container_host_ip()
    port = container.get_exposed_port(EXPOSED_PORT)

    user = container.username
    password = container.password
    db = container.dbname
    return f"{DRIVER_PREFIX}://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture(scope="session")
def postgres_url() -> Generator[str, None, None]:
    """Starts a temporary Postgres container for the whole test session
    and returns a SQLAlchemy-compatible DATABASE_URL.
    """
    with PostgresContainer("postgres:14-alpine") as pg:
        yield get_postgres_url_for_tests(pg)


@pytest.fixture(scope="session", autouse=True)
def init_test_db(postgres_url: str) -> None:
    """Initialize the database engine and sessionmaker for tests."""
    db_session_module.init_db_engine_and_sessionmaker(database_url=postgres_url)


@pytest.fixture(scope="session")
def engine() -> Engine:
    """Creates a SQLAlchemy engine connected to the testcontainer DB.
    """
    return db_session_module.ENGINE


@pytest.fixture(scope="session", autouse=True)
def apply_migrations(postgres_url: str) -> None:
    """Apply Alembic migrations to the test DB once at the start.
    This ensures your migrations are always valid.
    """
    alembic_cfg = Config(ALEMBIC_INI_PATH.as_posix())
    # Ensure alembic uses the test DB URL
    alembic_cfg.set_main_option("sqlalchemy.url", postgres_url)

    command.upgrade(alembic_cfg, "head")


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provides a DB session per test, isolated by a transaction rollback.
    In the tests pass this fixture as an argument to get a session.
    Note: Unlike production this does NOT need to be passed as a context manager.
    """
    connection = db_session_module.ENGINE.connect()
    transaction = connection.begin()
    session_local = db_session_module.sessionmaker(bind=connection, autoflush=False, autocommit=False, future=True)

    session = session_local()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def test_client(engine: Engine) -> Generator[TestClient, None, None]:
    """
    Use in FastAPI tests.
    - Overrides get_db_connection so all requests use the same per-test Session
    - Provides SAVEPOINT isolation even if the endpoint code commits
    """
    connection = engine.connect()
    transaction = connection.begin()

    session_local = db_session_module.sessionmaker(bind=connection, autoflush=False, autocommit=False, future=True)
    session = session_local()

    # Start a SAVEPOINT so app code can commit without ending the outer transaction
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess: Session, trans: RootTransaction) -> None:
        # If the nested tx ended, reopen it so the next commit still only affects a SAVEPOINT
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    def _override_get_db_connection() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[db_session_module.get_db_connection] = _override_get_db_connection

    # Use context manager so FastAPI lifespan/startup runs
    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()
