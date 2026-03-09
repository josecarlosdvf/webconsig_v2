from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.models.notification import Notification


class NotificationGateway:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        title: str,
        message: str,
        sender: str,
        recipient: str,
        category: str,
        metadata: dict,
    ) -> Notification:
        notification = Notification(
            title=title,
            message=message,
            sender=sender,
            recipient=recipient,
            category=category,
            metadata_json=json.dumps(metadata, default=str),
        )
        self.db.add(notification)
        self.db.flush()
        return notification

    def list_for_recipient(self, *, recipient: str, limit: int = 100, unread_only: bool = False) -> list[Notification]:
        query = self.db.query(Notification).filter(Notification.recipient == recipient)
        if unread_only:
            query = query.filter(Notification.read_at.is_(None))
        return query.order_by(Notification.created_at.desc()).limit(limit).all()

    def unread_total(self, *, recipient: str) -> int:
        return (
            self.db.query(func.count(Notification.id))
            .filter(Notification.recipient == recipient, Notification.read_at.is_(None))
            .scalar()
            or 0
        )

    def get_by_id(self, *, notification_id: str, recipient: str) -> Notification | None:
        return (
            self.db.query(Notification)
            .filter(Notification.id == notification_id, Notification.recipient == recipient)
            .first()
        )

    def mark_read(self, *, notification: Notification) -> Notification:
        if notification.read_at is None:
            notification.read_at = datetime.utcnow()
        self.db.flush()
        return notification

    def mark_all_read(self, *, recipient: str) -> int:
        items = self.db.query(Notification).filter(Notification.recipient == recipient, Notification.read_at.is_(None)).all()
        now = datetime.utcnow()
        for item in items:
            item.read_at = now
        self.db.flush()
        return len(items)
