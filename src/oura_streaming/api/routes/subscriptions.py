"""Webhook subscription management endpoints."""

from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...config import get_settings
from ...services.oura_client import get_oura_client

router = APIRouter()

SUBSCRIPTION_URL = "https://api.ouraring.com/v2/webhook/subscription"


class CreateSubscription(BaseModel):
    """Request body for creating a webhook subscription."""

    callback_url: str
    verification_token: str
    data_type: str
    event_type: str = "create"


def _headers(access_token: str) -> dict:
    """Build headers required by Oura webhook subscription API."""
    settings = get_settings()
    return {
        "Authorization": f"Bearer {access_token}",
        "x-client-id": settings.oura_client_id,
        "x-client-secret": settings.oura_client_secret,
    }


@router.get("/subscriptions")
async def list_subscriptions() -> JSONResponse:
    """List all active webhook subscriptions."""
    client = get_oura_client()
    if not client.is_authenticated:
        raise HTTPException(status_code=401, detail="Not authenticated. Visit /auth/login first.")

    async with client.http_client() as http:
        response = await http.get(
            SUBSCRIPTION_URL,
            headers=_headers(client.token.access_token),
        )
        if not response.is_success:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return JSONResponse(content=response.json())


@router.post("/subscriptions")
async def create_subscription(sub: CreateSubscription) -> JSONResponse:
    """Create a new webhook subscription with Oura."""
    client = get_oura_client()
    if not client.is_authenticated:
        raise HTTPException(status_code=401, detail="Not authenticated. Visit /auth/login first.")

    async with client.http_client() as http:
        response = await http.post(
            SUBSCRIPTION_URL,
            headers=_headers(client.token.access_token),
            json=sub.model_dump(),
        )
        # Return full response details for debugging
        try:
            body = response.json()
        except Exception:
            body = response.text
        return JSONResponse(content={
            "oura_status_code": response.status_code,
            "oura_response": body,
        })


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: str = Path(...)) -> JSONResponse:
    """Delete a webhook subscription."""
    client = get_oura_client()
    if not client.is_authenticated:
        raise HTTPException(status_code=401, detail="Not authenticated. Visit /auth/login first.")

    async with client.http_client() as http:
        response = await http.delete(
            f"{SUBSCRIPTION_URL}/{subscription_id}",
            headers=_headers(client.token.access_token),
        )
        if not response.is_success:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return JSONResponse(content={"status": "deleted", "id": subscription_id})
