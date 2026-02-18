"""Databricks SQL-backed event store writing to a Delta table.

Implements the same interface as the existing SQLite EventStore, but persists
to a Delta table via the SQL Statement Execution API. Subscription notifications
remain in-process so the dashboard continues to update in real time.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import AsyncGenerator, List, Optional
from uuid import uuid4

from ..config import Settings
from ..models.webhook import StoredEvent, WebhookEvent
from .dbsql_client import DBSQLClient, DBSQLConfig


def _sql_escape(val: Optional[str]) -> str:
    if val is None:
        return "NULL"
    return "'" + str(val).replace("'", "''") + "'"


class WarehouseEventStore:
    def __init__(self, settings: Settings):
        if not (settings.databricks_host and settings.databricks_http_path and settings.databricks_token):
            raise ValueError(
                "Databricks SQL configuration missing: set DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN"
            )
        self.settings = settings
        self.client = DBSQLClient(
            DBSQLConfig(
                host=settings.databricks_host,
                http_path=settings.databricks_http_path,
                token=settings.databricks_token,
            )
        )
        self.table = settings.delta_table
        self._subscribers: list[asyncio.Queue] = []
        self._init_lock = asyncio.Lock()
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            # Create Delta table if not exists
            create = f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
              id STRING,
              received_at TIMESTAMP,
              data_type STRING,
              event_type STRING,
              user_id STRING,
              payload STRING
            ) USING DELTA
            """
            await self.client.execute(create)
            self._initialized = True

    async def add(self, event: WebhookEvent) -> StoredEvent:
        await self._ensure_initialized()
        event_id = str(uuid4())
        received_at = datetime.now(UTC)
        payload_json = event.model_dump_json()

        insert = (
            "INSERT INTO "
            f"{self.table} (id, received_at, data_type, event_type, user_id, payload) VALUES ("
            f"{_sql_escape(event_id)}, "
            f"{_sql_escape(received_at.isoformat())}, "
            f"{_sql_escape(event.data_type)}, "
            f"{_sql_escape(event.event_type)}, "
            f"{_sql_escape(event.user_id)}, "
            f"{_sql_escape(payload_json)}"
            ")"
        )
        await self.client.execute(insert)

        stored = StoredEvent(id=event_id, received_at=received_at, event=event)
        for queue in self._subscribers:
            await queue.put(stored)
        return stored

    async def subscribe(self) -> AsyncGenerator[StoredEvent, None]:
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers.remove(queue)

    async def get_recent(self, limit: int = 50) -> List[StoredEvent]:
        await self._ensure_initialized()
        sql = f"SELECT id, received_at, payload FROM {self.table} ORDER BY received_at DESC LIMIT {int(limit)}"
        rows = await self.client.execute(sql) or []
        events: List[StoredEvent] = []
        for row in rows:
            eid, rcv, payload = row
            try:
                event = WebhookEvent.model_validate_json(payload)
            except Exception:
                continue
            # Databricks returns timestamps as strings when using HTTP API
            try:
                received_at = datetime.fromisoformat(str(rcv).replace("Z", "+00:00"))
            except Exception:
                received_at = datetime.now(UTC)
            events.append(StoredEvent(id=eid, received_at=received_at, event=event))
        return events

    async def get_by_data_type(self, data_type: str, limit: int = 50) -> List[StoredEvent]:
        await self._ensure_initialized()
        sql = (
            f"SELECT id, received_at, payload FROM {self.table} "
            f"WHERE data_type = {_sql_escape(data_type)} ORDER BY received_at DESC LIMIT {int(limit)}"
        )
        rows = await self.client.execute(sql) or []
        events: List[StoredEvent] = []
        for row in rows:
            eid, rcv, payload = row
            try:
                event = WebhookEvent.model_validate_json(payload)
            except Exception:
                continue
            try:
                received_at = datetime.fromisoformat(str(rcv).replace("Z", "+00:00"))
            except Exception:
                received_at = datetime.now(UTC)
            events.append(StoredEvent(id=eid, received_at=received_at, event=event))
        return events

    async def count(self) -> int:
        await self._ensure_initialized()
        sql = f"SELECT COUNT(1) FROM {self.table}"
        rows = await self.client.execute(sql) or [[0]]
        return int(rows[0][0])

    async def clear(self) -> int:
        await self._ensure_initialized()
        total = await self.count()
        await self.client.execute(f"DELETE FROM {self.table} WHERE true")
        return total

    async def prune_old_events(self, days: int = 30) -> int:
        await self._ensure_initialized()
        cutoff = datetime.now(UTC) - timedelta(days=days)
        sql = f"DELETE FROM {self.table} WHERE received_at < {_sql_escape(cutoff.isoformat())}"
        await self.client.execute(sql)
        # Row counts for DELETE via API are not returned inline; recompute
        return 0

