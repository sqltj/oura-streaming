import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, patch, MagicMock
from oura_streaming.services.poller import run_poller
import asyncio

@pytest.mark.asyncio
async def test_run_poller_generalized():
    # Mock settings
    mock_settings = MagicMock()
    mock_settings.polling_enabled = True
    mock_settings.polling_interval_seconds = 1
    mock_settings.poll_lookback_days = 1
    mock_settings.poll_data_types = "daily_sleep,daily_readiness,workout"
    mock_settings.oura_initial_refresh_token = ""

    # Mock Store and Client
    mock_store = AsyncMock()
    mock_client = MagicMock()
    mock_client.token = MagicMock()
    mock_client.token.access_token = "fake_access_token"
    mock_client.token.is_expired = False
    mock_client.ensure_token_loaded = AsyncMock(return_value=mock_client.token)

    # Mock fetch function
    mock_records = [{"id": "123", "day": "2026-02-18"}]
    
    with patch("oura_streaming.services.poller.get_settings", return_value=mock_settings), \
         patch("oura_streaming.services.poller.get_event_store", return_value=mock_store), \
         patch("oura_streaming.services.poller.get_oura_client", return_value=mock_client), \
         patch("oura_streaming.services.poller._fetch_oura_data", AsyncMock(return_value=mock_records)) as mock_fetch:
        
        stop_event = asyncio.Event()
        
        # Run poller in a task and stop it quickly
        poller_task = asyncio.create_task(run_poller(stop_event))
        
        # Give it a moment to run one cycle
        await asyncio.sleep(0.5)
        stop_event.set()
        await poller_task
        
        # Verify fetch was called for all types
        assert mock_fetch.call_count == 3
        calls = [call.args[0] for call in mock_fetch.call_args_list]
        assert "daily_sleep" in calls
        assert "daily_readiness" in calls
        assert "workout" in calls
        
        # Verify store.add was called
        assert mock_store.add.call_count == 3
        added_event = mock_store.add.call_args_list[0].args[0]
        assert added_event.data["source"] == "poller"
        assert added_event.data["count"] == 1
        assert added_event.data["records"] == mock_records
