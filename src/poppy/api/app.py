from fastapi import Depends, FastAPI, status

from poppy.core.events import EventCreate, EventRead
from poppy.db.session import get_db_connection
from poppy.services.event_handlers import create_event
from sqlalchemy.orm import Session

app = FastAPI()


@app.get("/")
def read_root():
    return {"Poppy": "Your Popeye-powered secretary"}


@app.post("/event", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event_via_fastapi(payload: EventCreate, session: Session = Depends(get_db_connection)) -> EventRead:
    return create_event(session, payload)
