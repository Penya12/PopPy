from typing import Generator
import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

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


@pytest.fixture(scope="session")
def engine(postgres_url) -> Generator[Engine, None, None]:
    """
    Creates a SQLAlchemy engine connected to the testcontainer DB.
    """
    eng = create_engine(postgres_url, future=True)
    yield eng
    eng.dispose()


# @pytest.fixture(scope="session", autouse=True)
# def apply_migrations(postgres_url):
#     """
#     Apply Alembic migrations to the test DB once at the start.
#     This ensures your migrations are always valid.
#     """
#     os.environ["DATABASE_URL"] = postgres_url

#     # Option A: run alembic via its command API
#     from alembic import command
#     from alembic.config import Config

#     alembic_cfg = Config("alembic.ini")
#     # Ensure alembic uses the test DB URL
#     alembic_cfg.set_main_option("sqlalchemy.url", postgres_url)

#     command.upgrade(alembic_cfg, "head")


@pytest.fixture()
def db_session(engine: Engine):
    """
    Provides a DB session per test, isolated by a transaction rollback.
    """
    connection = engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection, autoflush=False, autocommit=False, future=True)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
