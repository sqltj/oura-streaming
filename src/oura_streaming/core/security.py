"""Security utilities for OAuth2 and webhook verification."""

import secrets
from datetime import UTC, datetime, timedelta
from functools import lru_cache

from ..models.auth import OAuthState


class StateStore:
    """In-memory store for OAuth2 state tokens (CSRF protection)."""

    def __init__(self, ttl_minutes: int = 10):
        self._states: dict[str, OAuthState] = {}
        self._ttl = timedelta(minutes=ttl_minutes)

    def create(self) -> str:
        """Generate and store a new state token."""
        state = secrets.token_urlsafe(32)
        self._states[state] = OAuthState(state=state)
        self._cleanup_expired()
        return state

    def verify(self, state: str) -> bool:
        """Verify and consume a state token."""
        if state not in self._states:
            return False

        oauth_state = self._states.pop(state)
        age = datetime.now(UTC) - oauth_state.created_at
        return age < self._ttl

    def _cleanup_expired(self) -> None:
        """Remove expired states."""
        now = datetime.now(UTC)
        expired = [
            s for s, data in self._states.items()
            if now - data.created_at >= self._ttl
        ]
        for s in expired:
            del self._states[s]


import hmac
import hashlib
from ..config import get_settings


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify that the webhook request came from Oura.
    
    Oura signs the request body with the webhook secret using HMAC-SHA256.
    """
    settings = get_settings()
    if not settings.oura_webhook_secret:
        # If no secret is configured, skip verification (useful for dev)
        return True

    expected_signature = hmac.new(
        settings.oura_webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


@lru_cache
def _get_state_store() -> StateStore:
    """Get singleton state store."""
    return StateStore()


def generate_state() -> str:
    """Generate a new OAuth2 state token."""
    return _get_state_store().create()


def verify_state(state: str) -> bool:
    """Verify an OAuth2 state token."""
    return _get_state_store().verify(state)
