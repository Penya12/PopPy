"""Routes for creating and modifying events in the Poppy API."""
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from poppy.core.events import EventCreate, EventRead
from poppy.db.session import get_db_connection
from poppy.services.event_handlers import create_event, list_week

router = APIRouter(prefix="/event", tags=["events"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_event_via_fastapi(payload: EventCreate, session: Annotated[Session, Depends(get_db_connection)]) -> EventRead:
    """Thin wrapper around `create_event` for FastAPI."""
    return create_event(session, payload)


@router.get("/week")
def get_events_in_week(session: Annotated[Session, Depends(get_db_connection)], anchor: date | None = None) -> list[EventRead]:
    """Thin wrapper around `list_week` for FastAPI."""
    return list_week(session, anchor=anchor)
