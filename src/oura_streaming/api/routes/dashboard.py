"""Dashboard and WebSocket routes."""

import json
from pathlib import Path

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates

from ...services.event_store import get_event_store

router = APIRouter()

# Setup templates
BASE_DIR = Path(__file__).parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/dashboard")
async def dashboard(request: Request):
    """Render the real-time dashboard."""
    store = get_event_store()
    recent_events = await store.get_recent(limit=50)
    total_events = await store.count()
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "events": recent_events,
            "total_events": total_events
        }
    )


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """Stream new events to connected clients via WebSocket."""
    await websocket.accept()
    store = get_event_store()
    
    try:
        async for event in store.subscribe():
            # Convert StoredEvent to dict, handling datetime serialization
            event_dict = event.model_dump()
            event_dict["received_at"] = event.received_at.isoformat()
            if event.event.timestamp:
                event_dict["event"]["timestamp"] = event.event.timestamp.isoformat()
                
            await websocket.send_text(json.dumps(event_dict))
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()
