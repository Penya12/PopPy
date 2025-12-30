"""Database models for PopPy application.
This is the direct mapping of the database schema using SQLAlchemy ORM.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Integer, Text, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from poppy.services.utils import utcnow


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Optional fields
    why: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(64)), nullable=False, default=list)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


EXPECTED_TABLES_IN_DB = {"events", "alembic_version"}
