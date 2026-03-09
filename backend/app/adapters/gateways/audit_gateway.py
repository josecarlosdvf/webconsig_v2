import json
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.models.audit import AuditEvent


class AuditGateway:
    def __init__(self, db: Session):
        self.db = db

    def append(
        self,
        *,
        area: str,
        action: str,
        actor: str,
        request_id: str,
        detail: dict,
        source: str = "backend",
        resource: str | None = None,
        resource_id: str | None = None,
        http_method: str | None = None,
        http_path: str | None = None,
        status_code: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        severity: str = "INFO",
    ) -> None:
        event = AuditEvent(
            area=area,
            action=action,
            actor=actor or "anonymous",
            request_id=request_id,
            source=source,
            resource=resource,
            resource_id=resource_id,
            http_method=http_method,
            http_path=http_path,
            status_code=status_code,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity.upper(),
            detail=json.dumps(detail, default=str),
        )
        self.db.add(event)

    def list_recent(
        self,
        *,
        limit: int = 100,
        area: str | None = None,
        actor: str | None = None,
        action: str | None = None,
        source: str | None = None,
        severity: str | None = None,
        http_path: str | None = None,
    ) -> list[AuditEvent]:
        query = self.db.query(AuditEvent)
        if area:
            query = query.filter(AuditEvent.area == area)
        if actor:
            query = query.filter(AuditEvent.actor == actor)
        if action:
            query = query.filter(AuditEvent.action == action)
        if source:
            query = query.filter(AuditEvent.source == source)
        if severity:
            query = query.filter(AuditEvent.severity == severity.upper())
        if http_path:
            query = query.filter(AuditEvent.http_path == http_path)
        return query.order_by(AuditEvent.created_at.desc()).limit(limit).all()

    def summary(
        self,
        *,
        starts_at: datetime | None = None,
        ends_at: datetime | None = None,
    ) -> dict:
        query = self.db.query(AuditEvent)
        if starts_at:
            query = query.filter(AuditEvent.created_at >= starts_at)
        if ends_at:
            query = query.filter(AuditEvent.created_at <= ends_at)

        total = query.count()

        by_area = (
            query.with_entities(AuditEvent.area, func.count(AuditEvent.id))
            .group_by(AuditEvent.area)
            .order_by(func.count(AuditEvent.id).desc())
            .limit(20)
            .all()
        )
        by_actor = (
            query.with_entities(AuditEvent.actor, func.count(AuditEvent.id))
            .group_by(AuditEvent.actor)
            .order_by(func.count(AuditEvent.id).desc())
            .limit(20)
            .all()
        )
        by_action = (
            query.with_entities(AuditEvent.action, func.count(AuditEvent.id))
            .group_by(AuditEvent.action)
            .order_by(func.count(AuditEvent.id).desc())
            .limit(20)
            .all()
        )

        return {
            "total": total,
            "by_area": [{"key": key, "count": count} for key, count in by_area],
            "by_actor": [{"key": key, "count": count} for key, count in by_actor],
            "by_action": [{"key": key, "count": count} for key, count in by_action],
        }
