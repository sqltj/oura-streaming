"""OAuth2 models for Oura API."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class OAuthToken(BaseModel):
    """OAuth2 token response from Oura."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None
    created_at: datetime = Field(default_factory=_utc_now)

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        if self.expires_in is None:
            return False
        elapsed = (datetime.now(UTC) - self.created_at).total_seconds()
        return elapsed >= self.expires_in


class OAuthState(BaseModel):
    """OAuth2 state for CSRF protection."""

    state: str
    created_at: datetime = Field(default_factory=_utc_now)
