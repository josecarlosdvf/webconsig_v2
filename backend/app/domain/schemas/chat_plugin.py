from __future__ import annotations

from pydantic import Field

from app.domain.schemas.common import StrictSchema


class ChatMessageCreateRequest(StrictSchema):
    room: str = Field(default="geral", min_length=2, max_length=40)
    message: str = Field(min_length=1, max_length=3000)


class ChatMessageListRequest(StrictSchema):
    room: str = Field(default="geral", min_length=2, max_length=40)
    limit: int = Field(default=50, ge=1, le=200)


class ChatPluginMessage(StrictSchema):
    room: str
    message: str
    actor: str
    created_at: str


class ChatMessageListResponse(StrictSchema):
    room: str
    items: list[ChatPluginMessage]
    total: int
