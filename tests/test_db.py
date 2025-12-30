from sqlalchemy import Engine, text
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from poppy.db.models import EXPECTED_TABLES_IN_DB


def test_mock_db_is_alive(db_session: Session) -> None:
    assert db_session.execute(text("SELECT 1")).scalar() == 1


def test_mock_db_has_events_table(engine: Engine) -> None:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    for expected_table in EXPECTED_TABLES_IN_DB:
        assert expected_table in table_names, f"{expected_table} table is missing in the test database"
