"""Zerobus Ingest streaming write sink for Oura webhook events.

Sends every stored event to a Databricks Delta table via gRPC in a background task.
The sink is disabled gracefully if credentials are not configured or the Protobuf
schema module has not been generated yet (see PLAN-zerobus.md Phase 2).

SDK note: version 0.3.0 uses zerobus.sdk.aio (not zerobus.sdk.asyncio as in 0.2.0 docs).
Two-stage await: `future = await stream.ingest_record(rec)` then `await future` for ACK.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import Settings
    from ..models.webhook import StoredEvent

logger = logging.getLogger(__name__)


class ZerobusEventSink:
    """Async Zerobus write sink. No-op when Zerobus is not configured."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._sdk = None
        self._stream = None
        self._proto_module = None

    async def start(self) -> None:
        """Open the stream. Called from FastAPI lifespan."""
        if not self.settings.zerobus_enabled:
            logger.info("Zerobus sink disabled (credentials not configured)")
            return

        try:
            from oura_streaming import oura_events_pb2  # generated in Phase 2
            self._proto_module = oura_events_pb2
        except ImportError:
            logger.warning(
                "Zerobus sink disabled: oura_events_pb2 not found. "
                "Run Phase 2 proto generation before enabling Zerobus."
            )
            return

        await self._init_stream()

    async def stop(self) -> None:
        """Flush and close the stream. Called from FastAPI lifespan."""
        if self._stream:
            try:
                await self._stream.flush()
                await self._stream.close()
            except Exception as e:
                logger.warning("Zerobus: error closing stream: %s", e)
            self._stream = None

    async def ingest(self, event: StoredEvent) -> bool:
        """Ingest one event. Returns True on success, False on failure.

        Designed to be called as a FastAPI BackgroundTask — never raises.
        """
        if self._stream is None or self._proto_module is None:
            return False

        record = self._to_proto(event)
        return await self._ingest_with_retry(record)

    # ── internal helpers ────────────────────────────────────────────────────

    async def _init_stream(self) -> None:
        from zerobus.sdk.aio.zerobus_sdk import ZerobusSdk
        from zerobus.sdk.shared import RecordType, StreamConfigurationOptions, TableProperties

        s = self.settings
        self._sdk = ZerobusSdk(s.zerobus_server_endpoint, s.databricks_workspace_url)

        descriptor = self._proto_module.OuraEvent.DESCRIPTOR
        options = StreamConfigurationOptions(record_type=RecordType.PROTO)
        table_props = TableProperties(s.zerobus_table_name, descriptor)

        self._stream = await self._sdk.create_stream(
            s.databricks_client_id, s.databricks_client_secret, table_props, options
        )
        logger.info("Zerobus stream opened → %s", s.zerobus_table_name)

    def _to_proto(self, event: StoredEvent):
        """Map StoredEvent → Protobuf message. TIMESTAMP → int64 microseconds."""
        def _to_us(dt) -> int:
            return int(dt.timestamp() * 1_000_000) if dt else 0

        return self._proto_module.OuraEvent(
            id=event.id,
            received_at=_to_us(event.received_at),
            data_type=event.event.data_type,
            event_type=event.event.event_type,
            user_id=event.event.user_id or "",
            payload=event.event.model_dump_json(),
        )

    async def _ingest_with_retry(self, record, max_retries: int = 3) -> bool:
        for attempt in range(max_retries):
            try:
                future = await self._stream.ingest_record(record)
                await future
                return True
            except Exception as e:
                err = str(e).lower()
                logger.warning("Zerobus ingest attempt %d/%d failed: %s", attempt + 1, max_retries, e)
                if "closed" in err or "connection" in err or "unavailable" in err:
                    await self.stop()
                    try:
                        await self._init_stream()
                    except Exception:
                        pass
                if attempt < max_retries - 1:
                    await _async_sleep(2 ** attempt)
        return False


async def _async_sleep(seconds: float) -> None:
    import asyncio
    await asyncio.sleep(seconds)
