"""Skeleton setup required for the fastAPI app."""
from fastapi import Depends, FastAPI, status
from sqlalchemy.orm import Session

from poppy.core.events import EventCreate, EventRead
from poppy.db.session import get_db_connection
from poppy.services.event_handlers import create_event

app = FastAPI()


@app.get("/")
def read_root() -> dict[str, str]:
    """Meant to be hit to check if the API is alive."""
    return {"Poppy": "Your Popeye-powered secretary"}


@app.post("/event", status_code=status.HTTP_201_CREATED)
def create_event_via_fastapi(payload: EventCreate, session: Session = Depends(get_db_connection)) -> EventRead:
    """Thin wrapper around create_event for FastAPI."""
    return create_event(session, payload)
