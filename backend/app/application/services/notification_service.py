from __future__ import annotations

import asyncio
import json
from datetime import datetime

from fastapi import HTTPException, status

from app.adapters.gateways.audit_gateway import AuditGateway
from app.adapters.gateways.notification_gateway import NotificationGateway
from app.core.notification_hub import publish_notification, subscribe_recipient, unsubscribe_recipient
from app.domain.models.notification import Notification
from app.domain.schemas.notification import NotificationCreateRequest, NotificationListResponse, NotificationResponse


class NotificationService:
    def __init__(self, *, gateway: NotificationGateway, audit_gateway: AuditGateway):
        self.gateway = gateway
        self.audit_gateway = audit_gateway

    @staticmethod
    def _to_response(item: Notification) -> NotificationResponse:
        try:
            metadata = json.loads(item.metadata_json)
        except Exception:
            metadata = {}

        return NotificationResponse(
            id=item.id,
            title=item.title,
            message=item.message,
            sender=item.sender,
            recipient=item.recipient,
            category=item.category,
            metadata=metadata,
            created_at=item.created_at,
            read_at=item.read_at,
            is_read=item.read_at is not None,
        )

    def send_notification(self, *, payload: NotificationCreateRequest, actor: str, request_id: str) -> NotificationResponse:
        created = self.gateway.create(
            title=payload.title,
            message=payload.message,
            sender=actor,
            recipient=payload.recipient,
            category=payload.category,
            metadata=payload.metadata,
        )

        self.audit_gateway.append(
            area="notifications",
            action="notification.sent",
            actor=actor,
            request_id=request_id,
            resource="notification",
            resource_id=created.id,
            severity="INFO",
            detail={"recipient": payload.recipient, "title": payload.title},
        )

        response = self._to_response(created)
        publish_notification(recipient=created.recipient, payload=response.model_dump(mode="json"))
        return response

    def list_for_actor(self, *, actor: str, limit: int, unread_only: bool) -> NotificationListResponse:
        items = self.gateway.list_for_recipient(recipient=actor, limit=limit, unread_only=unread_only)
        mapped = [self._to_response(item) for item in items]
        unread_total = self.gateway.unread_total(recipient=actor)
        return NotificationListResponse(items=mapped, total=len(mapped), unread_total=unread_total)

    def mark_read(self, *, actor: str, notification_id: str, request_id: str) -> NotificationResponse:
        item = self.gateway.get_by_id(notification_id=notification_id, recipient=actor)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificação não encontrada")

        self.gateway.mark_read(notification=item)
        self.audit_gateway.append(
            area="notifications",
            action="notification.read",
            actor=actor,
            request_id=request_id,
            resource="notification",
            resource_id=item.id,
            severity="INFO",
            detail={"notification_id": item.id},
        )
        return self._to_response(item)

    def mark_all_read(self, *, actor: str, request_id: str) -> dict:
        total = self.gateway.mark_all_read(recipient=actor)
        self.audit_gateway.append(
            area="notifications",
            action="notification.read_all",
            actor=actor,
            request_id=request_id,
            resource="notification",
            severity="INFO",
            detail={"count": total},
        )
        return {"updated": total}

    async def subscribe(self, *, actor: str, timeout_seconds: int = 20):
        queue = await subscribe_recipient(recipient=actor)
        try:
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=timeout_seconds)
                    yield item
                except asyncio.TimeoutError:
                    yield {
                        "event_type": "notification.heartbeat",
                        "timestamp": datetime.utcnow().isoformat(),
                        "payload": {"message": "heartbeat"},
                    }
        finally:
            await unsubscribe_recipient(recipient=actor, queue=queue)
