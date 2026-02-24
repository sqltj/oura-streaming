"""Response models for API endpoints (drives Orval TypeScript generation)."""

from datetime import datetime

from pydantic import BaseModel

from .webhook import StoredEvent


class HealthOut(BaseModel):
    status: str
    authenticated: bool
    events_stored: int


class AuthStatusOut(BaseModel):
    authenticated: bool
    token_expired: bool | None = None


class LogoutOut(BaseModel):
    status: str


class EventOut(BaseModel):
    """Flattened event for the frontend."""
    id: str
    received_at: datetime
    data_type: str
    event_type: str
    user_id: str | None = None
    timestamp: datetime | None = None
    data: dict | None = None


class EventListOut(BaseModel):
    count: int
    total_stored: int
    events: list[EventOut]


class ClearEventsOut(BaseModel):
    status: str
    count: int


class WebhookVerifyOut(BaseModel):
    challenge: str


class WebhookReceiveOut(BaseModel):
    status: str
    event_id: str
    data_type: str
    event_type: str


class SubscriptionOut(BaseModel):
    id: str
    callback_url: str | None = None
    data_type: str | None = None
    event_type: str | None = None
    expiration_time: str | None = None


class SubscriptionDeleteOut(BaseModel):
    status: str
    id: str


class CallbackOut(BaseModel):
    status: str
    token_type: str
    scope: str | None = None
    expires_in: int | None = None
