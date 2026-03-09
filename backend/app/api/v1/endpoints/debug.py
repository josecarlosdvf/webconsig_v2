from pydantic import Field
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.adapters.gateways.audit_gateway import AuditGateway
from app.api.deps import get_actor, get_db, get_request_id, require_permission
from app.core.debug_store import debug_summary, list_debug_events, push_debug_event
from app.domain.schemas.common import StrictSchema
from app.domain.schemas.debug import DebugEventListResponse, DebugEventResponse, DebugSummaryResponse

router = APIRouter(prefix="/debug", tags=["debug"])


class FrontendLogPayload(StrictSchema):
    level: str = Field(min_length=3, max_length=10)
    message: str = Field(min_length=1, max_length=2000)
    context: dict = Field(default_factory=dict)


@router.post("/frontend-log", summary="Ingestão de logs do frontend")
def ingest_frontend_log(
    payload: FrontendLogPayload,
    request: Request,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
    actor: str = Depends(get_actor),
    _: None = Depends(require_permission("api:/debug/frontend-log", "create")),
) -> dict:
    push_debug_event(
        source="frontend",
        level=payload.level,
        message=payload.message,
        context=payload.context,
        request_id=request_id,
        actor=actor,
        path=request.url.path,
    )

    AuditGateway(db).append(
        area="frontend",
        action=f"debug.{payload.level.lower()}",
        actor=actor,
        request_id=request_id,
        source="frontend",
        resource="ui",
        http_method=request.method,
        http_path=request.url.path,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        severity=payload.level.upper(),
        detail={"message": payload.message, "context": payload.context},
    )
    return {"accepted": True}


@router.get("/events", response_model=DebugEventListResponse, summary="Consultar eventos de debug")
def get_debug_events(
    limit: int = Query(default=200, ge=1, le=2000),
    source: str | None = Query(default=None),
    level: str | None = Query(default=None),
    _: None = Depends(require_permission("api:/debug/events", "view")),
) -> DebugEventListResponse:
    items = [DebugEventResponse(**item) for item in list_debug_events(limit=limit, source=source, level=level)]
    return DebugEventListResponse(items=items, total=len(items))


@router.get("/summary", response_model=DebugSummaryResponse, summary="Resumo operacional de debug")
def get_debug_summary(_: None = Depends(require_permission("api:/debug/summary", "view"))) -> DebugSummaryResponse:
    return DebugSummaryResponse(**debug_summary())
