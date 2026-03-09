from __future__ import annotations

from app.core.plugins.base import PluginBase


class EchoPlugin(PluginBase):
    @property
    def slug(self) -> str:
        return "sample-echo"

    @property
    def name(self) -> str:
        return "Sample Echo Plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    def run(self, *, task: str, payload: dict, context: dict) -> dict:
        if task == "echo":
            return {
                "message": payload.get("message", "echo"),
                "task": task,
                "actor": context.get("actor", "anonymous"),
            }
        if task == "health":
            return {"status": "ok", "plugin": self.slug}
        raise ValueError(f"Task não suportada: {task}")
