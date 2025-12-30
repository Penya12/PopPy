from unittest.mock import MagicMock

import pytest
from sqlalchemy import Engine, inspect, text
from sqlalchemy.orm import Session

import poppy.db.session as db_session_module
from poppy.db.models import EXPECTED_TABLES_IN_DB, Event


def test_mock_db_is_alive(db_session: Session) -> None:
    assert db_session.execute(text("SELECT 1")).scalar() == 1


def test_mock_db_has_events_table(engine: Engine) -> None:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    for expected_table in EXPECTED_TABLES_IN_DB:
        assert expected_table in table_names, f"{expected_table} table is missing in the test database"


def test_model_and_mock_db_events_table_match(engine: Engine) -> None:
    inspector = inspect(engine)
    columns_in_db = {col["name"] for col in inspector.get_columns("events")}
    columns_in_model = set(Event.__table__.columns.keys())
    assert columns_in_db == columns_in_model, (
        f"Mismatch in `{Event.__name__}` model and `{Event.__tablename__}` table columns in the test database {columns_in_db=}, {columns_in_model=}"
    )


def test_session_scope_closes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_session = MagicMock()
    monkeypatch.setattr(db_session_module, "get_session", lambda: mock_session)

    with db_session_module.session_scope() as s:
        assert s is mock_session

    mock_session.close.assert_called_once()


def test_get_db_connection_closes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_session = MagicMock()
    # Make get_session() return our fake session
    monkeypatch.setattr(db_session_module, "get_session", lambda: mock_session)

    # Consume the generator
    gen = db_session_module.get_db_connection()
    session = next(gen)
    assert session is mock_session

    # Finish the generator -> triggers finally block
    with pytest.raises(StopIteration):
        next(gen)

    # Assert cleanup happened
    mock_session.close.assert_called_once()

