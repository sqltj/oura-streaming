"""FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .api.routes import api_router
from .config import get_settings
from .core.database import init_db
from .services.event_store import get_event_store
from .services.poller import run_poller

settings = get_settings()


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
    # Initialize database
    await init_db()
    # Start background tasks
    task = asyncio.create_task(prune_task())
    stop = asyncio.Event()
    poller_task = asyncio.create_task(run_poller(stop))
    yield
    stop.set()
    task.cancel()
    poller_task.cancel()


app = FastAPI(
    title="Oura Webhook Receiver",
    description="Receives Oura Ring API v2 webhooks and stores events in SQLite",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": "Oura Webhook Receiver",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "dashboard": "/dashboard",
        "endpoints": {
            "auth": {
                "login": "GET /auth/login",
                "callback": "GET /auth/callback",
                "status": "GET /auth/status",
                "logout": "POST /auth/logout",
            },
            "webhooks": {
                "verify": "GET /webhooks?verification_token=...",
                "receive": "POST /webhooks",
                "events": "GET /events",
                "clear": "DELETE /events",
            },
            "realtime": {
                "dashboard": "GET /dashboard",
                "websocket": "WS /ws/events",
            },
        },
    }
