"""OAuth2 authentication endpoints."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from ...core.security import generate_state, verify_state
from ...models.responses import AuthStatusOut, CallbackOut, LogoutOut
from ...services.oura_client import get_oura_client

router = APIRouter()


@router.get("/login", operation_id="loginRedirect")
async def login() -> RedirectResponse:
    """Redirect to Oura OAuth2 authorization page."""
    client = get_oura_client()
    state = generate_state()
    auth_url = client.get_authorization_url(state)
    return RedirectResponse(url=auth_url)


@router.get("/callback", response_model=CallbackOut, operation_id="authCallback")
async def callback(
    code: str = Query(..., description="Authorization code from Oura"),
    state: str = Query(..., description="State parameter for CSRF protection"),
) -> CallbackOut:
    """Handle OAuth2 callback from Oura."""
    if not verify_state(state):
        raise HTTPException(status_code=400, detail="Invalid or expired state parameter")

    client = get_oura_client()

    try:
        token = await client.exchange_code(code)
        return CallbackOut(
            status="authenticated",
            token_type=token.token_type,
            scope=token.scope,
            expires_in=token.expires_in,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")


@router.get("/status", response_model=AuthStatusOut, operation_id="getAuthStatus")
async def auth_status() -> AuthStatusOut:
    """Check current authentication status."""
    client = get_oura_client()
    await client.ensure_token_loaded()
    return AuthStatusOut(
        authenticated=client.is_authenticated,
        token_expired=client.token.is_expired if client.token else None,
    )


@router.post("/logout", response_model=LogoutOut, operation_id="logout")
async def logout() -> LogoutOut:
    """Clear stored OAuth token from memory and database."""
    from sqlalchemy import delete
    from ...models.db import DBOAuthToken
    from ...core.database import AsyncSessionLocal

    client = get_oura_client()
    client.token = None

    async with AsyncSessionLocal() as session:
        await session.execute(delete(DBOAuthToken))
        await session.commit()

    return LogoutOut(status="logged_out")
