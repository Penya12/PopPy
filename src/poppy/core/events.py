"""The pydantic models which will be used by CLI and API in PopPy. These do not have to map to the DB models 1:1."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum, auto
from typing import Any

from pydantic import BaseModel, Field, model_validator


class EventKind(StrEnum):
    """Allowed events."""

    action = auto()
    decision = auto()
    idea = auto()
    paper = auto()
    note = auto()
    meeting = auto()


class EventCreate(BaseModel):
    """Controller (from MVC design) Used by both API and CLI to create events."""

    kind: EventKind
    text: str = Field(min_length=1)
    why: str | None = None
    source: str | None = None
    tags: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
    due_at: datetime | None = Field(default=None)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def check_due_at_for_meetings(self) -> EventCreate:
        """Ensure that meetings have a due_at field set."""
        if self.kind == EventKind.meeting and self.due_at is None:
            error_msg = "Meetings must have a due_at field set."
            raise ValueError(error_msg)
        return self


class EventRead(BaseModel):
    """Controller (from MVC design) Used by both API to send DB read events over HTTP."""

    id: int
    created_at: datetime
    kind: EventKind
    text: str
    why: str | None
    source: str | None
    tags: list[str]
    meta: dict[str, Any]
    due_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True, "frozen": True}
