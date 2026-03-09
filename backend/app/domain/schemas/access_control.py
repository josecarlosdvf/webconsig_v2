from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.domain.schemas.common import StrictSchema


class AccessResourcePayload(StrictSchema):
    resource_key: str = Field(min_length=3, max_length=200)
    resource_type: str = Field(min_length=2, max_length=30)
    name: str = Field(min_length=2, max_length=140)
    path: str | None = Field(default=None, max_length=240)
    http_method: str | None = Field(default=None, max_length=16)
    parent_key: str | None = Field(default=None, max_length=200)
    metadata: dict = Field(default_factory=dict)
    is_active: bool = True


class AccessResourceResponse(StrictSchema):
    id: str
    resource_key: str
    resource_type: str
    name: str
    path: str | None
    http_method: str | None
    parent_key: str | None
    metadata: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AccessResourceListResponse(StrictSchema):
    items: list[AccessResourceResponse]
    total: int = Field(ge=0)


class CasbinPolicyPayload(StrictSchema):
    priority: str = Field(default="100", min_length=1, max_length=10)
    subject: str = Field(min_length=3, max_length=120)
    resource_regex: str = Field(min_length=1, max_length=255)
    action_regex: str = Field(min_length=1, max_length=100)
    effect: str = Field(default="allow", pattern="^(allow|deny)$")


class CasbinPolicyResponse(StrictSchema):
    priority: str
    subject: str
    resource_regex: str
    action_regex: str
    effect: str


class CasbinPolicyListResponse(StrictSchema):
    items: list[CasbinPolicyResponse]
    total: int = Field(ge=0)


class CasbinGroupingPayload(StrictSchema):
    subject: str = Field(min_length=3, max_length=120)
    role: str = Field(min_length=3, max_length=120)


class CasbinGroupingResponse(StrictSchema):
    subject: str
    role: str


class CasbinGroupingListResponse(StrictSchema):
    items: list[CasbinGroupingResponse]
    total: int = Field(ge=0)


class EnforceCheckPayload(StrictSchema):
    subjects: str = Field(min_length=1)
    resource: str = Field(min_length=1)
    action: str = Field(min_length=1)


class EnforceCheckResponse(StrictSchema):
    allowed: bool
