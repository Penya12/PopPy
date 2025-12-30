from datetime import date, datetime, timedelta, timezone
from pathlib import Path

DEFAULT_ENV_FILE_PATH = Path(__file__).parents[3] / ".env"
ALEMBIC_INI_PATH = Path(__file__).parents[3] / "alembic.ini"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def week_bounds(anchor: date | None = None) -> tuple[datetime, datetime]:
    """
    ISO week (Mon..Mon). anchor defaults to today (UTC date).
    """
    if anchor is None:
        anchor = datetime.now(timezone.utc).date()
    monday = anchor - timedelta(days=anchor.weekday())
    start = datetime(monday.year, monday.month, monday.day, tzinfo=timezone.utc)
    end = start + timedelta(days=7)
    return start, end


def get_database_url_from_env_file(env_file_path: Path = DEFAULT_ENV_FILE_PATH) -> str:
    """Reads the DATABASE_URL from a given .env file."""
    if not env_file_path.exists():
        raise FileNotFoundError(f".env file not found at: {env_file_path}")

    with env_file_path.open() as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                return line.strip().split("=", 1)[1]
    raise ValueError("DATABASE_URL not found in the specified .env file.")