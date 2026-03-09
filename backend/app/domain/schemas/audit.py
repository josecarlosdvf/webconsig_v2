from datetime import datetime

from pydantic import Field

from app.domain.schemas.common import StrictSchema


class AuditEventResponse(StrictSchema):
    id: int
    area: str
    action: str
    actor: str
    request_id: str
    source: str
    resource: str | None = None
    resource_id: str | None = None
    http_method: str | None = None
    http_path: str | None = None
    status_code: int | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    severity: str
    detail: dict | list | str
    created_at: datetime


class AuditListResponse(StrictSchema):
    items: list[AuditEventResponse]
    total: int = Field(ge=0)


class AuditSummaryItem(StrictSchema):
    key: str
    count: int = Field(ge=0)


class AuditSummaryResponse(StrictSchema):
    total: int = Field(ge=0)
    by_area: list[AuditSummaryItem]
    by_actor: list[AuditSummaryItem]
    by_action: list[AuditSummaryItem]
