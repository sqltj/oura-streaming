"""SQLAlchemy models for persistence."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

from ..core.database import Base


class DBStoredEvent(Base):
    """Persistent storage for webhook events."""

    __tablename__ = "events"

    id = Column(String, primary_key=True)
    received_at = Column(DateTime, default=lambda: datetime.now(UTC))
    data_type = Column(String, index=True)
    event_type = Column(String)
    user_id = Column(String, index=True)
    # Use SQLite-specific JSON for better compatibility if needed, 
    # but SQLAlchemy's JSON works well with aiosqlite
    payload = Column(JSON)


class DBOAuthToken(Base):
    """Persistent storage for OAuth tokens."""

    __tablename__ = "tokens"

    # We only store one token for the "current" user in this single-user app
    id = Column(Integer, primary_key=True, default=1)
    access_token = Column(String, nullable=False)
    token_type = Column(String, default="Bearer")
    expires_in = Column(Integer)
    refresh_token = Column(String)
    scope = Column(String)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
