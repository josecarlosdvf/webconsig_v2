from datetime import datetime

from pydantic import Field

from app.domain.schemas.common import StrictSchema


class NotificationCreateRequest(StrictSchema):
    recipient: str = Field(min_length=2, max_length=100)
    title: str = Field(min_length=2, max_length=140)
    message: str = Field(min_length=1, max_length=2000)
    category: str = Field(default="info", min_length=2, max_length=40)
    metadata: dict = Field(default_factory=dict)


class NotificationResponse(StrictSchema):
    id: str
    title: str
    message: str
    sender: str
    recipient: str
    category: str
    metadata: dict
    created_at: datetime
    read_at: datetime | None = None
    is_read: bool


class NotificationListResponse(StrictSchema):
    items: list[NotificationResponse]
    total: int = Field(ge=0)
    unread_total: int = Field(ge=0)
