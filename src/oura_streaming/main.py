"""FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api.routes import api_router, ws_router
from .config import get_settings
from .core.database import init_db
from .services.event_store import get_event_store
from .services.poller import run_poller
from .services.zerobus_sink import ZerobusEventSink

settings = get_settings()

# React build output directory
STATIC_DIR = Path(__file__).parent.parent.parent / "static"


async def prune_task():
    """Background task to prune old events every 24 hours."""
    while True:
        try:
            store = get_event_store()
            count = await store.prune_old_events(days=30)
            if count > 0:
                print(f"Pruned {count} old events")
        except Exception as e:
            print(f"Error in prune task: {e}")
        await asyncio.sleep(24 * 3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the FastAPI application."""
    await init_db()
    zerobus = ZerobusEventSink(settings)
    await zerobus.start()
    app.state.zerobus = zerobus
    task = asyncio.create_task(prune_task())
    stop = asyncio.Event()
    poller_task = asyncio.create_task(run_poller(stop))
    yield
    stop.set()
    task.cancel()
    poller_task.cancel()
    await zerobus.stop()


app = FastAPI(
    title="Oura Webhook Receiver",
    description="Receives Oura Ring API v2 webhooks and stores events in SQLite",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# API routes at /api/*
app.include_router(api_router)

# WebSocket at /ws/*
app.include_router(ws_router)

# Serve React build if it exists (production)
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
