"""Pytest fixtures for Oura webhook receiver tests."""

import pytest
from fastapi.testclient import TestClient

from oura_streaming.main import app
from oura_streaming.services.event_store import EventStore


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def event_store():
    """Create fresh event store for testing."""
    return EventStore(max_events=100)
