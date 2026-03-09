from __future__ import annotations

import asyncio
from datetime import datetime
import json

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from app.api.deps import get_actor, get_notification_service, get_request_id
from app.application.services.notification_service import NotificationService
from app.core.notification_hub import subscribe_recipient, unsubscribe_recipient
from app.domain.schemas.notification import NotificationCreateRequest, NotificationListResponse, NotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse, summary="Listar notificações do usuário")
def list_notifications(
    limit: int = Query(default=50, ge=1, le=500),
    unread_only: bool = Query(default=False),
    actor: str = Depends(get_actor),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
    return service.list_for_actor(actor=actor, limit=limit, unread_only=unread_only)


@router.post("/send", response_model=NotificationResponse, summary="Enviar notificação para usuário")
def send_notification(
    payload: NotificationCreateRequest,
    actor: str = Depends(get_actor),
    request_id: str = Depends(get_request_id),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    return service.send_notification(payload=payload, actor=actor, request_id=request_id)


@router.patch("/{notification_id}/read", response_model=NotificationResponse, summary="Marcar notificação como lida")
def read_notification(
    notification_id: str,
    actor: str = Depends(get_actor),
    request_id: str = Depends(get_request_id),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    return service.mark_read(actor=actor, notification_id=notification_id, request_id=request_id)


@router.patch("/read-all", summary="Marcar todas notificações como lidas")
def read_all_notifications(
    actor: str = Depends(get_actor),
    request_id: str = Depends(get_request_id),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    return service.mark_all_read(actor=actor, request_id=request_id)


@router.websocket("/ws")
async def notifications_ws(websocket: WebSocket) -> None:
    actor = websocket.query_params.get("actor")
    if not actor:
        await websocket.close(code=1008, reason="actor query param required")
        return

    await websocket.accept()
    queue = await subscribe_recipient(recipient=actor)
    try:
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=20)
                await websocket.send_text(json.dumps(item, default=str))
            except asyncio.TimeoutError:
                await websocket.send_text(
                    json.dumps(
                        {
                            "event_type": "notification.heartbeat",
                            "timestamp": datetime.utcnow().isoformat(),
                            "payload": {"message": "heartbeat"},
                        }
                    )
                )
    except WebSocketDisconnect:
        return
    finally:
        await unsubscribe_recipient(recipient=actor, queue=queue)
