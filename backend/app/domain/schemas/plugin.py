from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.domain.schemas.common import StrictSchema


class PluginRegisterRequest(StrictSchema):
    slug: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=120)
    version: str = Field(min_length=1, max_length=32)
    module_path: str = Field(min_length=3, max_length=255)
    config: dict = Field(default_factory=dict)


class PluginStateUpdateRequest(StrictSchema):
    enabled: bool


class PluginRunTaskRequest(StrictSchema):
    task: str = Field(min_length=2, max_length=80)
    payload: dict = Field(default_factory=dict)


class PluginResponse(StrictSchema):
    id: int
    slug: str
    name: str
    version: str
    module_path: str
    enabled: bool
    config: dict
    created_at: datetime
    updated_at: datetime


class PluginListResponse(StrictSchema):
    items: list[PluginResponse]
    total: int


class PluginTaskLogResponse(StrictSchema):
    id: int
    plugin_id: int
    plugin_slug: str
    actor: str
    task: str
    success: bool
    request_id: str
    payload: dict | list | str
    result: dict | list | str
    error: str | None = None
    created_at: datetime


class PluginTaskLogListResponse(StrictSchema):
    items: list[PluginTaskLogResponse]
    total: int


class PluginRunTaskResponse(StrictSchema):
    success: bool
    result: dict
    error: str | None = None
