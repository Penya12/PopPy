from typing import Generator
import pytest
from sqlalchemy import Engine
from testcontainers.postgres import PostgresContainer
from alembic import command
from alembic.config import Config

import poppy.db.session as db_session_module
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
    """
    Starts a temporary Postgres container for the whole test session
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
    """
    Creates a SQLAlchemy engine connected to the testcontainer DB.
    """
    return db_session_module.ENGINE


@pytest.fixture(scope="session", autouse=True)
def apply_migrations(postgres_url):
    """
    Apply Alembic migrations to the test DB once at the start.
    This ensures your migrations are always valid.
    """
    alembic_cfg = Config(ALEMBIC_INI_PATH.as_posix())
    # Ensure alembic uses the test DB URL
    alembic_cfg.set_main_option("sqlalchemy.url", postgres_url)

    command.upgrade(alembic_cfg, "head")


@pytest.fixture()
def db_session():
    """
    Provides a DB session per test, isolated by a transaction rollback.
    In the tests pass this fixture as an argument to get a session.
    Note: Unlike production this does NOT need to be passed as a context manager.
    """
    connection = db_session_module.ENGINE.connect()
    transaction = connection.begin()
    SessionLocal = db_session_module.sessionmaker(bind=connection, autoflush=False, autocommit=False, future=True)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
