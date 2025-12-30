from datetime import date, datetime, timedelta, timezone


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
