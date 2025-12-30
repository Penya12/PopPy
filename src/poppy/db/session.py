"""Creates the engine and sessionmaker for DB access. Used by the entire application."""
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from poppy.services.utils import get_database_url_from_env_file

DATABASE_URL = get_database_url_from_env_file()
ENGINE: Engine | None = None
SESSION_LOCAL: sessionmaker | None = None


def init_db_engine_and_sessionmaker(database_url: str = DATABASE_URL) -> None:
    """Initialize the global ENGINE and SESSION_LOCAL variables."""
    global ENGINE, SESSION_LOCAL  # noqa: PLW0603
    ENGINE = create_engine(database_url, future=True, pool_pre_ping=True)
    SESSION_LOCAL = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, future=True)


def get_session() -> Session:  # noqa: D103
    if SESSION_LOCAL is None:
        msg="Database engine and sessionmaker not initialized. Call init_db_engine_and_sessionmaker() first."
        raise RuntimeError(msg)
    return SESSION_LOCAL()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a secure connection to the CLI, and prevent using the try...finally block everywhere."""
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def get_db_connection() -> Generator[Session, None, None]:
    """Yield a database session and ensures it is closed after use.
    This is intended for use with FastAPI's dependency injection system.
    """
    with session_scope() as session:
        yield session
