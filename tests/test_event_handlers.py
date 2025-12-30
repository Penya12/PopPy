from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from poppy.core.events import EventCreate
from poppy.db.models import Event
from poppy.services.event_handlers import create_event, list_events_between, list_week
from poppy.services.utils import week_bounds


def test_create_event(db_session: Session) -> None:
    # Tests the creation of an event in the database
    payload = EventCreate(
        kind="note",
        text="This is a test event",
        why="Testing event creation",
        source="unit_test",
        tags=["test", "unit"],
        meta={"key": "value"},
    )

    created_event = create_event(db_session, payload)
    assert created_event.id is not None

    fetched_event = db_session.get(Event, created_event.id)
    assert fetched_event is not None
    assert fetched_event.kind == payload.kind
    assert fetched_event.text == payload.text
    assert fetched_event.why == payload.why
    assert fetched_event.source == payload.source
    assert fetched_event.tags == payload.tags
    assert fetched_event.meta == payload.meta
    assert fetched_event.created_at == created_event.created_at


def test_list_events_between(db_session: Session) -> None:
    now = datetime.now(UTC)
    # Insert three events by directly setting created_at so the test is deterministic
    e1 = Event(kind="note", text="old", created_at=now - timedelta(days=10), tags=[], meta={})
    e2 = Event(kind="action", text="in range 1", created_at=now - timedelta(days=2), tags=[], meta={})
    e3 = Event(kind="action", text="in range 2", created_at=now - timedelta(days=1), tags=[], meta={})
    db_session.add_all([e1, e2, e3])
    db_session.commit()

    start_time_for_two_events = now - timedelta(days=3)
    expected_two_events = list_events_between(db_session, start=start_time_for_two_events, end=now)
    assert len(expected_two_events) == 2
    assert [e.id for e in expected_two_events] == [e2.id, e3.id]

    start_time_for_three_events = now - timedelta(days=11)
    expected_three_events = list_events_between(db_session, start=start_time_for_three_events, end=now)
    assert len(expected_three_events) == 3
    assert [e.id for e in expected_three_events] == [e1.id, e2.id, e3.id]

    # No events in this range
    start_time = now - timedelta(minutes=5)
    expected_empty_list = list_events_between(db_session, start=start_time, end=now)
    assert len(expected_empty_list) == 0


def test_list_week(db_session: Session) -> None:
    start_of_week, end_of_week = week_bounds()
    # Insert events in different weeks, only e2 and e3 are in the expected week
    e1 = Event(kind="note", text="last week", created_at=start_of_week - timedelta(days=1), tags=[], meta={})
    e2 = Event(kind="action", text="this week 1", created_at=start_of_week + timedelta(days=1), tags=[], meta={})
    e3 = Event(kind="action", text="this week 2", created_at=start_of_week + timedelta(days=3), tags=[], meta={})
    e4 = Event(kind="idea", text="next week", created_at=end_of_week + timedelta(days=1), tags=[], meta={})
    db_session.add_all([e1, e2, e3, e4])
    db_session.commit()

    events_this_week = list_week(db_session)
    assert len(events_this_week) == 2
    assert [e.id for e in events_this_week] == [e2.id, e3.id]
