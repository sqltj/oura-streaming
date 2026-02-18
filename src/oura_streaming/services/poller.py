"""Background Oura poller for Databricks Apps (no public ingress required).

Periodically pulls usercollection endpoints and stores them as events using the
configured event store (SQLite or Delta via warehouse). Uses a bootstrap refresh
token if no token is present in the DB.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta
from typing import List

import httpx

from ..config import get_settings
from ..models.webhook import WebhookEvent
from .event_store import get_event_store
from .oura_client import get_oura_client


async def _ensure_token():
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


async def _fetch_daily_sleep(access_token: str, start: date, end: date) -> List[dict]:
    params = {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.ouraring.com/v2/usercollection/daily_sleep",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])


async def run_poller(stop_event: asyncio.Event):
    settings = get_settings()
    if not getattr(settings, "polling_enabled", False):
        return

    interval = int(getattr(settings, "polling_interval_seconds", 300))
    lookback_days = int(getattr(settings, "poll_lookback_days", 1))
    data_types = str(getattr(settings, "poll_data_types", "daily_sleep")).split(",")
    data_types = [dt.strip() for dt in data_types if dt.strip()]

    store = get_event_store()
    client = get_oura_client()

    while not stop_event.is_set():
        try:
            await _ensure_token()
            token = client.token
            if not token or not token.access_token:
                # No token; skip this cycle
                await asyncio.sleep(interval)
                continue

            since = date.today() - timedelta(days=lookback_days)
            until = date.today()

            if "daily_sleep" in data_types:
                try:
                    records = await _fetch_daily_sleep(token.access_token, since, until)
                    if records:
                        event = WebhookEvent(
                            data_type="daily_sleep",
                            event_type="create",
                            data={"source": "poller", "records": records, "range": [since.isoformat(), until.isoformat()]},
                        )
                        await store.add(event)
                except Exception as e:
                    print(f"Poll daily_sleep failed: {e}")

        except Exception as loop_err:
            print(f"Poller loop error: {loop_err}")

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass

