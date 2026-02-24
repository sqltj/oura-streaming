"""Health check endpoint."""

from fastapi import APIRouter

from ...models.responses import HealthOut
from ...services.event_store import get_event_store
from ...services.oura_client import get_oura_client

router = APIRouter()


@router.get("/health", response_model=HealthOut, operation_id="getHealth")
async def health_check() -> HealthOut:
    """Return application health status."""
    event_store = get_event_store()
    oura_client = get_oura_client()

    await oura_client.ensure_token_loaded()

    return HealthOut(
        status="healthy",
        authenticated=oura_client.is_authenticated,
        events_stored=await event_store.count(),
    )
