from __future__ import annotations

import json
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.gateways.audit_gateway import AuditGateway
from app.adapters.gateways.plugin_gateway import PluginGateway
from app.core.debug_store import push_debug_event
from app.core.plugins.manager import PluginManager
from app.domain.schemas.plugin import PluginRegisterRequest, PluginRunTaskRequest, PluginRunTaskResponse


class PluginService:
    def __init__(self, *, db: Session):
        self.db = db
        self.gateway = PluginGateway(db)
        self.audit = AuditGateway(db)

    def discover_manifests(self) -> list[dict]:
        plugins_root = Path(__file__).resolve().parents[3] / "plugins"
        found: list[dict] = []
        for manifest in plugins_root.glob("*/manifest.json"):
            data = json.loads(manifest.read_text(encoding="utf-8"))
            found.append(data)
        return found

    def list_plugins(self):
        return self.gateway.list_plugins()

    def register_plugin(self, *, payload: PluginRegisterRequest, actor: str, request_id: str):
        if self.gateway.get_by_slug(payload.slug):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Plugin já registrado")

        plugin = self.gateway.create_plugin(
            slug=payload.slug,
            name=payload.name,
            version=payload.version,
            module_path=payload.module_path,
            config=payload.config,
        )
        self.audit.append(
            area="plugins",
            action="plugin.registered",
            actor=actor,
            request_id=request_id,
            source="backend",
            resource="plugin",
            resource_id=str(plugin.id),
            severity="INFO",
            detail={"slug": plugin.slug, "module_path": plugin.module_path},
        )
        push_debug_event(
            source="backend",
            level="INFO",
            message="plugin_registered",
            context={"plugin_id": plugin.id, "slug": plugin.slug},
            request_id=request_id,
            actor=actor,
            path="/plugins/register",
        )
        return plugin

    def set_state(self, *, plugin_id: int, enabled: bool, actor: str, request_id: str):
        plugin = self.gateway.get_by_id(plugin_id)
        if not plugin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin não encontrado")
        plugin.enabled = enabled
        self.db.flush()

        self.audit.append(
            area="plugins",
            action="plugin.state_changed",
            actor=actor,
            request_id=request_id,
            source="backend",
            resource="plugin",
            resource_id=str(plugin.id),
            severity="INFO",
            detail={"slug": plugin.slug, "enabled": plugin.enabled},
        )
        return plugin

    def run_task(self, *, plugin_id: int, payload: PluginRunTaskRequest, actor: str, request_id: str) -> PluginRunTaskResponse:
        plugin = self.gateway.get_by_id(plugin_id)
        if not plugin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin não encontrado")
        if not plugin.enabled:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Plugin está desabilitado")

        execution = PluginManager.execute(
            module_path=plugin.module_path,
            task=payload.task,
            payload=payload.payload,
            context={"actor": actor, "request_id": request_id, "plugin_slug": plugin.slug},
        )

        self.gateway.save_task_log(
            plugin_id=plugin.id,
            plugin_slug=plugin.slug,
            actor=actor,
            task=payload.task,
            success=execution.success,
            request_id=request_id,
            payload=payload.payload,
            result=execution.result,
            error=execution.error,
        )

        self.audit.append(
            area="plugins",
            action="plugin.task.executed",
            actor=actor,
            request_id=request_id,
            source="backend",
            resource="plugin_task",
            resource_id=str(plugin.id),
            severity="INFO" if execution.success else "ERROR",
            detail={
                "slug": plugin.slug,
                "task": payload.task,
                "success": execution.success,
                "error": execution.error,
            },
        )

        push_debug_event(
            source="backend",
            level="INFO" if execution.success else "ERROR",
            message="plugin_task_executed",
            context={
                "plugin_id": plugin.id,
                "plugin_slug": plugin.slug,
                "task": payload.task,
                "success": execution.success,
                "error": execution.error,
            },
            request_id=request_id,
            actor=actor,
            path=f"/plugins/{plugin.id}/tasks/run",
        )
        return PluginRunTaskResponse(success=execution.success, result=execution.result, error=execution.error)

    def list_logs(self, *, plugin_id: int, limit: int = 100):
        plugin = self.gateway.get_by_id(plugin_id)
        if not plugin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin não encontrado")
        return self.gateway.list_task_logs(plugin_id=plugin_id, limit=limit)
