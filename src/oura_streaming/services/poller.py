"""Background Oura poller for Databricks Apps (no public ingress required).

Periodically pulls usercollection endpoints and stores them as events using the
configured event store (SQLite or Delta via warehouse). Uses a bootstrap refresh
token if no token is present in the DB.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List

import httpx

from ..config import get_settings
from ..models.webhook import WebhookEvent
from .event_store import get_event_store
from .oura_client import get_oura_client

# Data types that use start_date/end_date parameters
DAILY_METRIC_TYPES = {
    "daily_sleep",
    "daily_readiness",
    "daily_activity",
    "daily_spo2",
    "daily_stress",
    "daily_cycle_phases",
    "sleep_time",
}

# Data types that use start_datetime/end_datetime parameters
DOCUMENT_METRIC_TYPES = {
    "sleep",
    "workout",
    "session",
    "tag",
    "enhanced_tag",
    "rest_mode_period",
    "ring_configuration",
}


async def _ensure_token():
    """Ensure we have a valid OAuth token, attempting a refresh if needed."""
    settings = get_settings()
    client = get_oura_client()
    token = await client.ensure_token_loaded()
    if token is None and getattr(settings, "oura_initial_refresh_token", ""):
        try:
            await client.refresh_token_with_value(settings.oura_initial_refresh_token)
            return
        except Exception as e:
            print(f"Poller bootstrap refresh failed: {e}")
            return
    if token and token.is_expired:
        try:
            await client.refresh_token()
        except Exception as e:
            print(f"Token refresh failed: {e}")


async def _fetch_oura_data(
    data_type: str, access_token: str, start: datetime, end: datetime
) -> List[Dict[str, Any]]:
    """Generic fetcher for Oura v2 usercollection endpoints."""
    params = {}
    if data_type in DAILY_METRIC_TYPES:
        params["start_date"] = start.date().isoformat()
        params["end_date"] = end.date().isoformat()
    else:
        # Document types use ISO8601 datetimes
        params["start_datetime"] = start.isoformat()
        params["end_datetime"] = end.isoformat()

    # Ring configuration doesn't support time filtering
    if data_type == "ring_configuration":
        params = {}

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.ouraring.com/v2/usercollection/{data_type}",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])


async def run_poller(stop_event: asyncio.Event):
    """Background loop to poll Oura API and ingest events."""
    settings = get_settings()
    if not getattr(settings, "polling_enabled", False):
        return

    interval = int(getattr(settings, "polling_interval_seconds", 300))
    lookback_days = int(getattr(settings, "poll_lookback_days", 1))

    # Get requested data types, default to daily_sleep if none specified
    raw_types = str(getattr(settings, "poll_data_types", "daily_sleep")).split(",")
    data_types = [dt.strip() for dt in raw_types if dt.strip()]

    store = get_event_store()
    client = get_oura_client()

    print(f"Starting Oura poller (interval: {interval}s, types: {data_types})")

    while not stop_event.is_set():
        try:
            await _ensure_token()
            token = client.token
            if not token or not token.access_token:
                # No token available yet; wait and retry
                await asyncio.sleep(min(interval, 60))
                continue

            # Calculate time range for this poll
            end_dt = datetime.now(UTC)
            start_dt = end_dt - timedelta(days=lookback_days)

            for dt in data_types:
                try:
                    records = await _fetch_oura_data(dt, token.access_token, start_dt, end_dt)
                    if records:
                        # Wrap records as a mock webhook event
                        # Note: In a real webhook, each record would likely be its own event,
                        # but for polling we batch them to minimize DB writes and dashboard noise.
                        event = WebhookEvent(
                            data_type=dt,
                            event_type="create",
                            data={
                                "source": "poller",
                                "count": len(records),
                                "records": records,
                                "range": [start_dt.isoformat(), end_dt.isoformat()]
                            },
                            user_id="polled_user",
                        )
                        await store.add(event)
                        print(f"Poller ingested {len(records)} records for {dt}")
                except Exception as e:
                    print(f"Poll for {dt} failed: {e}")

        except Exception as loop_err:
            print(f"Poller loop error: {loop_err}")

        # Wait for next interval or stop signal
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass
