from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_actor, get_plugin_service, get_request_id, require_permission
from app.application.services.plugin_service import PluginService
from app.domain.schemas.plugin import (
    PluginListResponse,
    PluginRegisterRequest,
    PluginResponse,
    PluginRunTaskRequest,
    PluginRunTaskResponse,
    PluginStateUpdateRequest,
    PluginTaskLogListResponse,
    PluginTaskLogResponse,
)

router = APIRouter(prefix="/plugins", tags=["plugins"])


def _to_response(item) -> PluginResponse:
    return PluginResponse(
        id=item.id,
        slug=item.slug,
        name=item.name,
        version=item.version,
        module_path=item.module_path,
        enabled=item.enabled,
        config=item.config or {},
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("", response_model=PluginListResponse, summary="Listar plugins")
def list_plugins(
    service: PluginService = Depends(get_plugin_service),
    _: None = Depends(require_permission("api:/api/v1/plugins", "view")),
) -> PluginListResponse:
    items = [_to_response(item) for item in service.list_plugins()]
    return PluginListResponse(items=items, total=len(items))


@router.get("/discover", summary="Descobrir plugins locais")
def discover_plugins(
    service: PluginService = Depends(get_plugin_service),
    _: None = Depends(require_permission("api:/api/v1/plugins/discover", "view")),
) -> dict:
    items = service.discover_manifests()
    return {"items": items, "total": len(items)}


@router.post("/register", response_model=PluginResponse, summary="Registrar plugin")
def register_plugin(
    payload: PluginRegisterRequest,
    service: PluginService = Depends(get_plugin_service),
    actor: str = Depends(get_actor),
    request_id: str = Depends(get_request_id),
    _: None = Depends(require_permission("api:/api/v1/plugins/register", "create")),
) -> PluginResponse:
    plugin = service.register_plugin(payload=payload, actor=actor, request_id=request_id)
    return _to_response(plugin)


@router.patch("/{plugin_id}/state", response_model=PluginResponse, summary="Habilitar/Desabilitar plugin")
def set_plugin_state(
    plugin_id: int,
    payload: PluginStateUpdateRequest,
    service: PluginService = Depends(get_plugin_service),
    actor: str = Depends(get_actor),
    request_id: str = Depends(get_request_id),
    _: None = Depends(require_permission("api:/api/v1/plugins/{plugin_id}/state", "edit")),
) -> PluginResponse:
    plugin = service.set_state(plugin_id=plugin_id, enabled=payload.enabled, actor=actor, request_id=request_id)
    return _to_response(plugin)


@router.post("/{plugin_id}/tasks/run", response_model=PluginRunTaskResponse, summary="Executar tarefa de plugin")
def run_plugin_task(
    plugin_id: int,
    payload: PluginRunTaskRequest,
    service: PluginService = Depends(get_plugin_service),
    actor: str = Depends(get_actor),
    request_id: str = Depends(get_request_id),
    _: None = Depends(require_permission("api:/api/v1/plugins/{plugin_id}/tasks/run", "execute")),
) -> PluginRunTaskResponse:
    return service.run_task(plugin_id=plugin_id, payload=payload, actor=actor, request_id=request_id)


@router.get("/{plugin_id}/tasks/logs", response_model=PluginTaskLogListResponse, summary="Listar logs de tarefas")
def list_plugin_task_logs(
    plugin_id: int,
    limit: int = Query(default=100, ge=1, le=1000),
    service: PluginService = Depends(get_plugin_service),
    _: None = Depends(require_permission("api:/api/v1/plugins/{plugin_id}/tasks/logs", "view")),
) -> PluginTaskLogListResponse:
    logs = service.list_logs(plugin_id=plugin_id, limit=limit)
    items: list[PluginTaskLogResponse] = []
    for item in logs:
        try:
            payload = json.loads(item.payload)
        except Exception:
            payload = item.payload
        try:
            result = json.loads(item.result)
        except Exception:
            result = item.result

        items.append(
            PluginTaskLogResponse(
                id=item.id,
                plugin_id=item.plugin_id,
                plugin_slug=item.plugin_slug,
                actor=item.actor,
                task=item.task,
                success=item.success,
                request_id=item.request_id,
                payload=payload,
                result=result,
                error=item.error,
                created_at=item.created_at,
            )
        )

    return PluginTaskLogListResponse(items=items, total=len(items))
