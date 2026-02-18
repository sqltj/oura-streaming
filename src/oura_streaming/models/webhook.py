"""Webhook payload models for Oura API v2."""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)

# All 14 data types supported by Oura webhooks
DataType = Literal[
    "tag",
    "enhanced_tag",
    "workout",
    "session",
    "sleep",
    "daily_sleep",
    "daily_readiness",
    "daily_activity",
    "daily_spo2",
    "sleep_time",
    "rest_mode_period",
    "ring_configuration",
    "daily_stress",
    "daily_cycle_phases",
]

EventType = Literal["create", "update", "delete"]


class WebhookEvent(BaseModel):
    """Oura webhook event payload."""

    data_type: DataType
    event_type: EventType
    data: dict[str, Any] | None = None
    user_id: str | None = None
    timestamp: datetime | None = None


class StoredEvent(BaseModel):
    """Event with metadata for storage."""

    id: str
    received_at: datetime = Field(default_factory=_utc_now)
    event: WebhookEvent
