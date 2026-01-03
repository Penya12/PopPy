"""Manipulate event-related data and handle event-driven operations in PopPy."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from poppy.core.events import EventCreate, EventKind
from poppy.db.models import Event
from poppy.services.utils import utcnow, week_bounds


def create_event(session: Session, payload: EventCreate) -> Event:
    """Use in API and the CLI to create events in the DB."""
    ev = Event(
        kind=payload.kind,
        text=payload.text,
        why=payload.why,
        source=payload.source,
        tags=payload.tags,
        meta=payload.meta,
        due_at=payload.due_at,
    )
    session.add(ev)
    session.commit()
    session.refresh(ev)
    return ev


def get_event_by_id(session: Session, event_id: int) -> Event | None:
    """Fetch an event by its ID."""
    return session.get(Event, event_id)


def list_events_between(session: Session, start: datetime, end: datetime) -> list[Event]:
    """List events created on or after `start` and before `end`."""
    stmt = (
        select(Event)
        .where(Event.created_at >= start, Event.created_at < end)
        .order_by(Event.created_at.asc(), Event.id.asc())
    )
    return list(session.execute(stmt).scalars())


def list_week(session: Session, anchor: date | None = None) -> list[Event]:
    """List events created during the week of `anchor` date.
    Defaults to current week if `anchor` is None.
    """
    start, end = week_bounds(anchor)
    return list_events_between(session, start, end)


def list_todo(session: Session, *, pending_only: bool = True) -> list[Event]:
    """List all actions as a todo list.

    If `pending_only` is True, only returns actions which have a non-null `due_at`
    and null `completed_at`.
    """
    # Actions are the only kind of event in todo list
    stmt = select(Event).where(Event.kind == EventKind.action.value)

    # Pending only = the event has a non-null `due_at`` field and null `completed_at` field
    if pending_only:
        stmt = stmt.where(Event.due_at.is_not(None)).where(Event.completed_at.is_(None))

    stmt = stmt.order_by(Event.created_at.asc(), Event.id.asc())
    return list(session.execute(stmt).scalars())


def list_todo_split_by_current_week(session: Session) -> dict[str, list[Event]]:
    """List all pending actions, split into 'this_week' and 'later' based on `created_at`."""
    actions = list_todo(session, pending_only=True)
    this_week_actions = []
    later_actions = []
    start_of_week, end_of_week = week_bounds()
    for ev in actions:
        if start_of_week <= ev.created_at < end_of_week:
            this_week_actions.append(ev)
        else:
            later_actions.append(ev)

    return {"created_this_week": this_week_actions, "older": later_actions}


def mark_event_completed(session: Session, event_id: str, completed_at: datetime | None = None) -> Event:
    """Mark an event as completed by setting its `completed_at` field."""
    event = get_event_by_id(session, event_id)
    if event is None:
        msg = f"Event with ID {event_id} not found."
        raise ValueError(msg)

    event.completed_at = completed_at or utcnow()
    session.add(event)
    session.commit()
    session.refresh(event)
    return event
