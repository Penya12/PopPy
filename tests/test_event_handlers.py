from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from poppy.core.events import EventCreate
from poppy.db.models import Event
from poppy.services.event_handlers import (
    create_event,
    list_events_between,
    list_todo,
    list_todo_split_by_current_week,
    list_week,
)
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


def test_list_todo_ignores_non_actions(db_session: Session) -> None:
    now = datetime.now(UTC)
    action_event = Event(
        kind="action",
        text="pending action",
        due_at=now + timedelta(days=2),
        completed_at=None
    )
    note_event = Event(kind="note", text="just a note")
    idea_event = Event(kind="idea", text="just an idea")
    db_session.add_all([action_event, note_event, idea_event])
    db_session.commit()

    # This should pass regardless of pending_only value, since it's the only action
    [todo_action] = list_todo(db_session, pending_only=False)
    assert todo_action.id == action_event.id


def test_list_todo_pending_only(db_session: Session) -> None:
    now = datetime.now(UTC)
    pending_action = Event(
        kind="action",
        text="pending action",
        due_at=now + timedelta(days=2),
        completed_at=None
    )
    completed_action = Event(
        kind="action",
        text="completed action",
        due_at=now - timedelta(days=1),
        completed_at=now - timedelta(hours=1)
    )
    no_due_action = Event(
        kind="action",
        text="no due action",
        due_at=None,
        completed_at=None
    )
    db_session.add_all([pending_action, completed_action, no_due_action])
    db_session.commit()

    [todo_action] = list_todo(db_session)
    assert todo_action.id == pending_action.id


def test_todo_split_by_current_week(db_session: Session) -> None:
    start_of_week, end_of_week = week_bounds()
    this_week_action = Event(
        kind="action",
        text="created_this_week",
        created_at=start_of_week + timedelta(days=1),
        due_at=end_of_week + timedelta(days=2),
        completed_at=None
    )
    later_action = Event(
        kind="action",
        text="created_last_week",
        created_at=start_of_week - timedelta(days=3),
        due_at=end_of_week + timedelta(days=3),
        completed_at=None
    )
    note = Event(
        kind="note",
        text="just a note - should be ignored",
    )
    db_session.add_all([this_week_action, later_action, note])
    db_session.commit()

    split_todo = list_todo_split_by_current_week(db_session)
    assert len(split_todo["created_this_week"]) == 1
    assert split_todo["created_this_week"][0].id == this_week_action.id
    assert len(split_todo["older"]) == 1
    assert split_todo["older"][0].id == later_action.id
