from sqlalchemy import text
from sqlalchemy.orm import Session

def test_mock_db_is_alive(db_session: Session) -> None:
    assert db_session.execute(text("SELECT 1")).scalar() == 1
