from pydantic import Field

from app.domain.schemas.common import StrictSchema


class DebugEventResponse(StrictSchema):
    timestamp: str
    source: str
    level: str
    message: str
    context: dict
    request_id: str | None = None
    actor: str | None = None
    path: str | None = None


class DebugEventListResponse(StrictSchema):
    items: list[DebugEventResponse]
    total: int = Field(ge=0)


class DebugSummaryResponse(StrictSchema):
    total: int = Field(ge=0)
    by_source: dict[str, int]
    by_level: dict[str, int]
