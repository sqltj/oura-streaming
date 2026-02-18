"""Async HTTP client for Oura API OAuth2 flow with persistence."""

from contextlib import asynccontextmanager
from functools import lru_cache
from urllib.parse import urlencode

import httpx
from sqlalchemy import select

from ..config import Settings, get_settings
from ..core.database import AsyncSessionLocal
from ..models.auth import OAuthToken
from ..models.db import DBOAuthToken


class OuraClient:
    """Client for Oura API OAuth2 operations with SQLite persistence."""

    # OAuth2 scopes available in Oura API
    SCOPES = ["personal", "daily", "heartrate", "workout", "session", "tag", "spo2"]

    def __init__(self, settings: Settings, session_factory=AsyncSessionLocal):
        self.settings = settings
        self.session_factory = session_factory
        self._token: OAuthToken | None = None
        self._loaded = False

    @asynccontextmanager
    async def http_client(self):
        """Create an async HTTP client."""
        async with httpx.AsyncClient() as client:
            yield client

    async def ensure_token_loaded(self) -> OAuthToken | None:
        """Ensure token is loaded from database."""
        if not self._loaded:
            await self.load_token()
        return self._token

    async def load_token(self) -> OAuthToken | None:
        """Load token from database."""
        async with self.session_factory() as session:
            stmt = select(DBOAuthToken).where(DBOAuthToken.id == 1)
            result = await session.execute(stmt)
            db_token = result.scalar_one_or_none()

            if db_token:
                self._token = OAuthToken(
                    access_token=db_token.access_token,
                    token_type=db_token.token_type,
                    expires_in=db_token.expires_in,
                    refresh_token=db_token.refresh_token,
                    scope=db_token.scope,
                    created_at=db_token.created_at,
                )
            else:
                self._token = None
            
            self._loaded = True
            return self._token

    async def save_token(self, token: OAuthToken) -> None:
        """Save token to database."""
        self._token = token
        async with self.session_factory() as session:
            # We use id=1 for the single current token
            stmt = select(DBOAuthToken).where(DBOAuthToken.id == 1)
            result = await session.execute(stmt)
            db_token = result.scalar_one_or_none()

            if not db_token:
                db_token = DBOAuthToken(id=1)
                session.add(db_token)

            db_token.access_token = token.access_token
            db_token.token_type = token.token_type
            db_token.expires_in = token.expires_in
            db_token.refresh_token = token.refresh_token
            db_token.scope = token.scope
            db_token.created_at = token.created_at
            
            await session.commit()

    def get_authorization_url(self, state: str) -> str:
        """Generate Oura OAuth2 authorization URL."""
        params = {
            "client_id": self.settings.oura_client_id,
            "redirect_uri": self.settings.oura_redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "state": state,
        }
        return f"{self.settings.oura_auth_url}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> OAuthToken:
        """Exchange authorization code for access token and save it."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.settings.oura_token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": self.settings.oura_client_id,
                    "client_secret": self.settings.oura_client_secret,
                    "redirect_uri": self.settings.oura_redirect_uri,
                },
            )
            response.raise_for_status()
            data = response.json()
            token = OAuthToken(**data)
            await self.save_token(token)
            return token

    async def refresh_token(self) -> OAuthToken:
        """Refresh an expired access token."""
        token = await self.ensure_token_loaded()
        if not token or not token.refresh_token:
            raise ValueError("No refresh token available")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.settings.oura_token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": token.refresh_token,
                    "client_id": self.settings.oura_client_id,
                    "client_secret": self.settings.oura_client_secret,
                },
            )
            response.raise_for_status()
            data = response.json()
            new_token = OAuthToken(**data)
            await self.save_token(new_token)
        return new_token

    async def refresh_token_with_value(self, refresh_token: str) -> OAuthToken:
        """Refresh using a provided refresh token (bootstrap path)."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.settings.oura_token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.settings.oura_client_id,
                    "client_secret": self.settings.oura_client_secret,
                },
            )
            response.raise_for_status()
            data = response.json()
            new_token = OAuthToken(**data)
            await self.save_token(new_token)
            return new_token

    @property
    def token(self) -> OAuthToken | None:
        """Get current token."""
        return self._token

    @token.setter
    def token(self, value: OAuthToken | None) -> None:
        """Set current token (Note: this does not persist automatically)."""
        self._token = value

    @property
    def is_authenticated(self) -> bool:
        """Check if client has a valid (non-expired) token."""
        return self._token is not None and not self._token.is_expired


@lru_cache
def get_oura_client() -> OuraClient:
    """Get singleton Oura client instance."""
    return OuraClient(get_settings())
