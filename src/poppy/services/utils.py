"""Helpers for various utilities used across the project."""
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

DEFAULT_ENV_FILE_PATH = Path(__file__).parents[3] / ".env"
ALEMBIC_INI_PATH = Path(__file__).parents[3] / "alembic.ini"


def utcnow() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(UTC)


def week_bounds(anchor: date | None = None) -> tuple[datetime, datetime]:
    """ISO week (Mon..Mon). anchor defaults to today (UTC date)."""
    if anchor is None:
        anchor = datetime.now(UTC).date()
    monday = anchor - timedelta(days=anchor.weekday())
    start = datetime(monday.year, monday.month, monday.day, tzinfo=UTC)
    end = start + timedelta(days=7)
    return start, end


def get_database_url_from_env_file(env_file_path: Path = DEFAULT_ENV_FILE_PATH) -> str:
    """Read the DATABASE_URL from a given .env file."""
    if not env_file_path.exists():
        msg = f".env file not found at: {env_file_path}"
        raise FileNotFoundError(msg)

    with env_file_path.open() as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                return line.strip().split("=", 1)[1]
    msg = "DATABASE_URL not found in the specified .env file."
    raise ValueError(msg)
