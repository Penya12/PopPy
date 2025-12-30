"""Manipulate event-related data and handle event-driven operations in PopPy."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from poppy.db.models import Event
from poppy.core.events import EventCreate
from poppy.services.utils import week_bounds


def create_event(session: Session, payload: EventCreate) -> Event:
    """The API and the CLI should use this to create events in the DB."""
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


def list_events_between(session: Session, start: datetime, end: datetime) -> list[Event]:
    """Lists events created on or after `start` and before `end`."""
    stmt = (
        select(Event)
        .where(Event.created_at >= start, Event.created_at < end)
        .order_by(Event.created_at.asc(), Event.id.asc())
    )
    return list(session.execute(stmt).scalars())


def list_week(session: Session, anchor: date | None = None) -> list[Event]:
    start, end = week_bounds(anchor)
    return list_events_between(session, start, end)
