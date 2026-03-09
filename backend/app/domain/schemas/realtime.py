from pydantic import Field

from app.domain.schemas.common import StrictSchema


class RealtimeEvent(StrictSchema):
    event_type: str
    timestamp: str
    payload: dict


class RealtimeEventListResponse(StrictSchema):
    items: list[RealtimeEvent]
    total: int = Field(ge=0)
