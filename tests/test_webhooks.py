"""Tests for webhook endpoints."""

import pytest

from oura_streaming.core.database import init_db
from oura_streaming.main import app
from oura_streaming.models.webhook import WebhookEvent
from oura_streaming.services.event_store import EventStore


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    yield


@pytest.fixture
async def client():
    from httpx import ASGITransport, AsyncClient
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestHealth:
    async def test_health_check(self, client):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "authenticated" in data
        assert "events_stored" in data


@pytest.mark.asyncio
class TestWebhookVerification:
    async def test_verify_webhook_echoes_challenge(self, client):
        token = "test-token"
        challenge = "test-challenge"
        response = await client.get(f"/api/webhooks?verification_token={token}&challenge={challenge}")
        assert response.status_code == 200
        assert response.json() == {"challenge": challenge}


@pytest.mark.asyncio
class TestWebhookReceive:
    async def test_receive_webhook_event(self, client):
        event = {
            "data_type": "daily_sleep",
            "event_type": "create",
            "data": {"score": 85},
        }
        response = await client.post("/api/webhooks", json=event)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
        assert data["data_type"] == "daily_sleep"
        assert data["event_type"] == "create"
        assert "event_id" in data

    async def test_receive_webhook_all_data_types(self, client):
        data_types = [
            "tag", "enhanced_tag", "workout", "session", "sleep",
            "daily_sleep", "daily_readiness", "daily_activity",
            "daily_spo2", "sleep_time", "rest_mode_period",
            "ring_configuration", "daily_stress", "daily_cycle_phases",
        ]
        for dt in data_types:
            response = await client.post("/api/webhooks", json={
                "data_type": dt,
                "event_type": "create",
            })
            assert response.status_code == 200, f"Failed for {dt}"


@pytest.mark.asyncio
class TestEventStore:
    async def test_add_and_retrieve_events(self):
        store = EventStore()
        event = WebhookEvent(data_type="daily_sleep", event_type="create")

        stored = await store.add(event)
        assert stored.id is not None
        assert stored.event == event

        events = await store.get_recent()
        assert len(events) >= 1

    async def test_filter_by_data_type(self):
        store = EventStore()
        await store.add(WebhookEvent(data_type="sleep", event_type="create"))
        await store.add(WebhookEvent(data_type="workout", event_type="create"))

        sleep_events = await store.get_by_data_type("sleep")
        assert len(sleep_events) >= 1
        assert all(e.event.data_type == "sleep" for e in sleep_events)


@pytest.mark.asyncio
class TestEventsEndpoint:
    async def test_get_events(self, client):
        await client.post("/api/webhooks", json={"data_type": "sleep", "event_type": "create"})
        await client.post("/api/webhooks", json={"data_type": "workout", "event_type": "create"})

        response = await client.get("/api/events")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "events" in data

    async def test_filter_events_by_data_type(self, client):
        await client.post("/api/webhooks", json={"data_type": "sleep", "event_type": "create"})
        await client.post("/api/webhooks", json={"data_type": "workout", "event_type": "create"})

        response = await client.get("/api/events?data_type=sleep")
        assert response.status_code == 200
        data = response.json()
        for event in data["events"]:
            assert event["data_type"] == "sleep"

    async def test_clear_events(self, client):
        await client.post("/api/webhooks", json={"data_type": "sleep", "event_type": "create"})
        response = await client.delete("/api/events")
        assert response.status_code == 200
        assert response.json()["status"] == "cleared"
