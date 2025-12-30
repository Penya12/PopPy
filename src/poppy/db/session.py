# src/poppy/db/session.py
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from pathlib import Path


DEFAULT_ENV_FILE_PATH = Path(__file__).parents[3] / ".env"


def get_database_url_from_env_file(env_file_path: Path = DEFAULT_ENV_FILE_PATH) -> str:
    """Reads the DATABASE_URL from a given .env file."""
    if not env_file_path.exists():
        raise FileNotFoundError(f".env file not found at: {env_file_path}")

    with env_file_path.open() as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                return line.strip().split("=", 1)[1]
    raise ValueError("DATABASE_URL not found in the specified .env file.")


DATABASE_URL = get_database_url_from_env_file()
ENGINE = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
SESSION_LOCAL = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, future=True)


def get_session() -> Session:
    return SESSION_LOCAL()
