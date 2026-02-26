"""Webhook endpoints for receiving Oura events."""

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, Request

from ...core.security import verify_webhook_signature
from ...models.responses import (
    ClearEventsOut,
    EventListOut,
    EventOut,
    WebhookReceiveOut,
    WebhookVerifyOut,
)
from ...models.webhook import WebhookEvent
from ...services.event_store import get_event_store

router = APIRouter()


@router.get("/webhooks", response_model=WebhookVerifyOut, operation_id="verifyWebhook")
async def verify_webhook(
    verification_token: str = Query("", description="Verification token from Oura"),
    challenge: str = Query("", description="Challenge token from Oura to echo back"),
) -> WebhookVerifyOut:
    """
    Webhook verification endpoint.

    Oura sends a GET with both verification_token and challenge params.
    Echo back the challenge value to confirm endpoint ownership.
    """
    return WebhookVerifyOut(challenge=challenge)


@router.post("/webhooks", response_model=WebhookReceiveOut, operation_id="receiveWebhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_oura_signature: str = Header(None, alias="x-oura-signature"),
) -> WebhookReceiveOut:
    """
    Receive webhook events from Oura.

    Verifies signature, stores in SQLite, and fires Zerobus ingest as a background task.
    """
    body = await request.body()

    if not verify_webhook_signature(body, x_oura_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        event = WebhookEvent.model_validate_json(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    store = get_event_store()
    stored = await store.add(event)

    sink = getattr(request.app.state, "zerobus", None)
    if sink is not None:
        background_tasks.add_task(sink.ingest, stored)

    return WebhookReceiveOut(
        status="received",
        event_id=stored.id,
        data_type=event.data_type,
        event_type=event.event_type,
    )


@router.get("/events", response_model=EventListOut, operation_id="listEvents")
async def get_events(
    limit: int = Query(50, ge=1, le=500, description="Max events to return"),
    data_type: str | None = Query(None, description="Filter by data type"),
) -> EventListOut:
    """Get recent webhook events from database."""
    store = get_event_store()

    if data_type:
        events = await store.get_by_data_type(data_type, limit=limit)
    else:
        events = await store.get_recent(limit)

    return EventListOut(
        count=len(events),
        total_stored=await store.count(),
        events=[
            EventOut(
                id=e.id,
                received_at=e.received_at,
                data_type=e.event.data_type,
                event_type=e.event.event_type,
                user_id=e.event.user_id,
                timestamp=e.event.timestamp,
                data=e.event.data,
            )
            for e in events
        ],
    )


@router.delete("/events", response_model=ClearEventsOut, operation_id="clearEvents")
async def clear_events() -> ClearEventsOut:
    """Clear all stored events."""
    store = get_event_store()
    cleared = await store.clear()
    return ClearEventsOut(status="cleared", count=cleared)
