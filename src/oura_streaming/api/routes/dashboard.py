"""WebSocket route for real-time event streaming."""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...services.event_store import get_event_store

router = APIRouter()


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """Stream new events to connected clients via WebSocket."""
    await websocket.accept()
    store = get_event_store()

    try:
        async for event in store.subscribe():
            event_dict = event.model_dump()
            event_dict["received_at"] = event.received_at.isoformat()
            if event.event.timestamp:
                event_dict["event"]["timestamp"] = event.event.timestamp.isoformat()

            await websocket.send_text(json.dumps(event_dict))
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()
