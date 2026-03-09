from __future__ import annotations

import json
from sqlalchemy.orm import Session

from app.domain.models.plugin import PluginModule, PluginTaskLog


class PluginGateway:
    def __init__(self, db: Session):
        self.db = db

    def list_plugins(self) -> list[PluginModule]:
        return self.db.query(PluginModule).order_by(PluginModule.name.asc()).all()

    def get_by_id(self, plugin_id: int) -> PluginModule | None:
        return self.db.query(PluginModule).filter(PluginModule.id == plugin_id).first()

    def get_by_slug(self, slug: str) -> PluginModule | None:
        return self.db.query(PluginModule).filter(PluginModule.slug == slug).first()

    def create_plugin(self, *, slug: str, name: str, version: str, module_path: str, config: dict) -> PluginModule:
        plugin = PluginModule(
            slug=slug,
            name=name,
            version=version,
            module_path=module_path,
            config=config,
            enabled=True,
        )
        self.db.add(plugin)
        self.db.flush()
        return plugin

    def save_task_log(
        self,
        *,
        plugin_id: int,
        plugin_slug: str,
        actor: str,
        task: str,
        success: bool,
        request_id: str,
        payload: dict,
        result: dict,
        error: str | None,
    ) -> PluginTaskLog:
        log = PluginTaskLog(
            plugin_id=plugin_id,
            plugin_slug=plugin_slug,
            actor=actor,
            task=task,
            success=success,
            request_id=request_id,
            payload=json.dumps(payload, default=str),
            result=json.dumps(result, default=str),
            error=error,
        )
        self.db.add(log)
        self.db.flush()
        return log

    def list_task_logs(self, *, plugin_id: int, limit: int = 100) -> list[PluginTaskLog]:
        return (
            self.db.query(PluginTaskLog)
            .filter(PluginTaskLog.plugin_id == plugin_id)
            .order_by(PluginTaskLog.created_at.desc())
            .limit(limit)
            .all()
        )
