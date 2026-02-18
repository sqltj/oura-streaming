"""Event storage abstraction with a SQLite implementation.

Default backend is SQLite (SQLAlchemy). In Databricks environments, set
`STORAGE_BACKEND=warehouse` and provide Databricks SQL config to persist
events into a Delta table via the SQL Statement Execution API.
"""

import asyncio
from datetime import UTC, datetime
from functools import lru_cache
from typing import AsyncGenerator
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..core.database import AsyncSessionLocal
from ..models.db import DBStoredEvent
from ..models.webhook import StoredEvent, WebhookEvent


class EventStore:
    """Persistent event store using SQLite with real-time notifications."""

    def __init__(self, session_factory=AsyncSessionLocal):
        self.session_factory = session_factory
        self._subscribers: list[asyncio.Queue] = []

    async def add(self, event: WebhookEvent) -> StoredEvent:
        """Store a webhook event in SQLite and notify subscribers."""
        event_id = str(uuid4())
        received_at = datetime.now(UTC)

        async with self.session_factory() as session:
            db_event = DBStoredEvent(
                id=event_id,
                received_at=received_at,
                data_type=event.data_type,
                event_type=event.event_type,
                user_id=event.user_id,
                payload=event.model_dump(),
            )
            session.add(db_event)
            await session.commit()

        stored = StoredEvent(
            id=event_id,
            received_at=received_at,
            event=event
        )

        # Notify subscribers
        for queue in self._subscribers:
            await queue.put(stored)

        return stored

    async def subscribe(self) -> AsyncGenerator[StoredEvent, None]:
        """Subscribe to new events."""
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers.remove(queue)

    async def get_recent(self, limit: int = 50) -> list[StoredEvent]:
        """Get most recent events from database."""
        async with self.session_factory() as session:
            stmt = select(DBStoredEvent).order_by(DBStoredEvent.received_at.desc()).limit(limit)
            result = await session.execute(stmt)
            db_events = result.scalars().all()

            return [
                StoredEvent(
                    id=e.id,
                    received_at=e.received_at,
                    event=WebhookEvent(**e.payload)
                )
                for e in db_events
            ]

    async def get_by_data_type(self, data_type: str, limit: int = 50) -> list[StoredEvent]:
        """Filter events by data type."""
        async with self.session_factory() as session:
            stmt = (
                select(DBStoredEvent)
                .where(DBStoredEvent.data_type == data_type)
                .order_by(DBStoredEvent.received_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            db_events = result.scalars().all()

            return [
                StoredEvent(
                    id=e.id,
                    received_at=e.received_at,
                    event=WebhookEvent(**e.payload)
                )
                for e in db_events
            ]

    async def count(self) -> int:
        """Get total event count."""
        async with self.session_factory() as session:
            stmt = select(func.count()).select_from(DBStoredEvent)
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def clear(self) -> int:
        """Clear all events and return count cleared."""
        async with self.session_factory() as session:
            total = await self.count()
            await session.execute(delete(DBStoredEvent))
            await session.commit()
            return total

    async def prune_old_events(self, days: int = 30) -> int:
        """Prune events older than specified days."""
        cutoff = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff = cutoff.replace(tzinfo=None) # SQLite storage usually handles this
        
        # Actually SQLite stores as naive usually if not handled, 
        # but let's just use timedelta
        from datetime import timedelta
        cutoff = datetime.now(UTC) - timedelta(days=days)

        async with self.session_factory() as session:
            stmt = delete(DBStoredEvent).where(DBStoredEvent.received_at < cutoff)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount


def _maybe_warehouse_store():
    """Factory that returns a WarehouseEventStore if configured, else None."""
    settings = get_settings()
    if settings.storage_backend.lower() == "warehouse":
        try:
            from .warehouse_store import WarehouseEventStore

            return WarehouseEventStore(settings)
        except Exception as e:
            # Fall back to SQLite if misconfigured, but log-friendly error
            print(f"Warehouse backend unavailable, falling back to SQLite: {e}")
    return None


@lru_cache
def get_event_store():
    """Return the configured event store (warehouse or sqlite)."""
    store = _maybe_warehouse_store()
    if store is not None:
        return store
    return EventStore()
