from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from app.api.deps import require_permission
from app.core.realtime_hub import list_recent_events, publish_event, subscribe, unsubscribe
from app.domain.schemas.realtime import RealtimeEvent, RealtimeEventListResponse

router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.get("/events", response_model=RealtimeEventListResponse, summary="Consultar eventos de tempo real")
def get_realtime_events(
    limit: int = Query(default=100, ge=1, le=1000),
    event_type: str | None = Query(default=None),
    _: None = Depends(require_permission("api:/api/v1/realtime/events", "view")),
) -> RealtimeEventListResponse:
    items = [RealtimeEvent(**item) for item in list_recent_events(limit=limit, event_type=event_type)]
    return RealtimeEventListResponse(items=items, total=len(items))


@router.get("/htmx/audit-feed", response_class=HTMLResponse, summary="Fragmento HTMX de feed em tempo real")
def get_htmx_audit_feed(
    limit: int = Query(default=10, ge=1, le=100),
    _: None = Depends(require_permission("api:/api/v1/realtime/htmx/audit-feed", "view")),
) -> HTMLResponse:
    items = list_recent_events(limit=limit)
    lines: list[str] = ["<ul class='list-group'>"]
    for item in items:
        payload = item.get("payload", {})
        actor = payload.get("actor", "system")
        action = payload.get("action", payload.get("message", "event"))
        lines.append(
            "<li class='list-group-item d-flex justify-content-between align-items-center'>"
            f"<span><strong>{item.get('event_type')}</strong> • {action} • {actor}</span>"
            f"<small>{item.get('timestamp')}</small>"
            "</li>"
        )
    lines.append("</ul>")

    response = HTMLResponse("".join(lines))
    response.headers["HX-Trigger"] = "realtime-feed-updated"
    return response


@router.websocket("/ws")
async def websocket_realtime(websocket: WebSocket) -> None:
    await websocket.accept()
    queue = await subscribe()

    publish_event(event_type="system.connection", payload={"message": "websocket_connected"})

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15)
                await websocket.send_text(json.dumps(event, default=str))
            except asyncio.TimeoutError:
                await websocket.send_text(
                    json.dumps(
                        {
                            "event_type": "system.heartbeat",
                            "timestamp": None,
                            "payload": {"message": "heartbeat"},
                        }
                    )
                )
    except WebSocketDisconnect:
        pass
    finally:
        await unsubscribe(queue)
        publish_event(event_type="system.connection", payload={"message": "websocket_disconnected"})
