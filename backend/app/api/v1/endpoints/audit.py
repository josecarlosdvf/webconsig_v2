import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.adapters.gateways.audit_gateway import AuditGateway
from app.api.deps import get_db
from app.domain.schemas.audit import AuditEventResponse, AuditListResponse, AuditSummaryResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events", response_model=AuditListResponse, summary="Consultar trilha de auditoria")
def list_audit_events(
    limit: int = Query(default=100, ge=1, le=500),
    area: str | None = Query(default=None),
    actor: str | None = Query(default=None),
    action: str | None = Query(default=None),
    source: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    http_path: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> AuditListResponse:
    records = AuditGateway(db).list_recent(
        limit=limit,
        area=area,
        actor=actor,
        action=action,
        source=source,
        severity=severity,
        http_path=http_path,
    )

    items = []
    for record in records:
        parsed_detail: dict | list | str
        try:
            parsed_detail = json.loads(record.detail)
        except (TypeError, json.JSONDecodeError):
            parsed_detail = record.detail

        items.append(
            AuditEventResponse(
                id=record.id,
                area=record.area,
                action=record.action,
                actor=record.actor,
                request_id=record.request_id,
                source=record.source,
                resource=record.resource,
                resource_id=record.resource_id,
                http_method=record.http_method,
                http_path=record.http_path,
                status_code=record.status_code,
                ip_address=record.ip_address,
                user_agent=record.user_agent,
                severity=record.severity,
                detail=parsed_detail,
                created_at=record.created_at,
            )
        )

    return AuditListResponse(items=items, total=len(items))


@router.get("/summary", response_model=AuditSummaryResponse, summary="Resumo de auditoria para relatórios")
def audit_summary(
    starts_at: datetime | None = Query(default=None),
    ends_at: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> AuditSummaryResponse:
    summary = AuditGateway(db).summary(starts_at=starts_at, ends_at=ends_at)
    return AuditSummaryResponse(**summary)
