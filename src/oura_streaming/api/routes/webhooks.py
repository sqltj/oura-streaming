"""Webhook endpoints for receiving Oura events."""

from fastapi import APIRouter, Header, HTTPException, Query, Request

from ...core.security import verify_webhook_signature
from ...models.webhook import StoredEvent, WebhookEvent
from ...services.event_store import get_event_store

router = APIRouter()


@router.get("/webhooks")
async def verify_webhook(
    verification_token: str = Query("", description="Verification token from Oura"),
    challenge: str = Query("", description="Challenge token from Oura to echo back"),
) -> dict:
    """
    Webhook verification endpoint.

    Oura sends a GET with both verification_token and challenge params.
    Echo back the challenge value to confirm endpoint ownership.
    """
    return {"challenge": challenge}


@router.post("/webhooks")
async def receive_webhook(
    request: Request,
    x_oura_signature: str = Header(None, alias="x-oura-signature")
) -> dict:
    """
    Receive webhook events from Oura.

    Verifies signature and stores events in SQLite.
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

    return {
        "status": "received",
        "event_id": stored.id,
        "data_type": event.data_type,
        "event_type": event.event_type,
    }


@router.get("/events")
async def get_events(
    limit: int = Query(50, ge=1, le=500, description="Max events to return"),
    data_type: str | None = Query(None, description="Filter by data type"),
) -> dict:
    """Get recent webhook events from database."""
    store = get_event_store()

    if data_type:
        events = await store.get_by_data_type(data_type, limit=limit)
    else:
        events = await store.get_recent(limit)

    return {
        "count": len(events),
        "total_stored": await store.count(),
        "events": [e.model_dump() for e in events],
    }


@router.delete("/events")
async def clear_events() -> dict:
    """Clear all stored events."""
    store = get_event_store()
    cleared = await store.clear()
    return {"status": "cleared", "count": cleared}
