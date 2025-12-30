"""Manipulate event-related data and handle event-driven operations in PopPy."""
# src/poppy/services/events.py
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from poppy.db.models import Event
from poppy.core.events import EventCreate


def create_event(session: Session, payload: EventCreate) -> Event:
    ev = Event(
        kind=payload.kind,
        text=payload.text,
        why=payload.why,
        source=payload.source,
        tags=payload.tags,
        meta=payload.meta,
    )
    session.add(ev)
    session.commit()
    session.refresh(ev)
    return ev


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


def list_events_between(session: Session, start: datetime, end: datetime) -> list[Event]:
    stmt = (
        select(Event)
        .where(Event.created_at >= start, Event.created_at < end)
        .order_by(Event.created_at.asc(), Event.id.asc())
    )
    return list(session.execute(stmt).scalars())


def list_week(session: Session, anchor: date | None = None) -> list[Event]:
    start, end = week_bounds(anchor)
    return list_events_between(session, start, end)
