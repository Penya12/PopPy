"""The pydantic models which will be used by CLI and API in PopPy. These do not have to map to the DB models 1:1."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum, auto
from typing import Any, Optional

from pydantic import BaseModel, Field

class EventKind(StrEnum):
    action = auto()
    decision = auto()
    idea = auto()
    paper = auto()
    note = auto()
    meeting = auto()


class EventCreate(BaseModel):
    kind: EventKind
    text: str = Field(min_length=1)
    why: Optional[str] = None
    source: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class EventRead(BaseModel):
    id: int
    created_at: datetime
    kind: EventKind
    text: str
    why: Optional[str]
    source: Optional[str]
    tags: list[str]
    meta: dict[str, Any]

    model_config = {"from_attributes": True}
