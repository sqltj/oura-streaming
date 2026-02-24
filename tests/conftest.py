"""Pytest fixtures for Oura webhook receiver tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from oura_streaming.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
