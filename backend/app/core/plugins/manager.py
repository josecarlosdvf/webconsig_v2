from __future__ import annotations

import importlib
from dataclasses import dataclass

from app.core.plugins.base import PluginBase


@dataclass
class PluginExecutionResult:
    success: bool
    result: dict
    error: str | None = None


class PluginManager:
    @staticmethod
    def load(module_path: str) -> PluginBase:
        if ":" not in module_path:
            raise ValueError("module_path deve seguir formato 'package.module:ClassName'")

        module_name, class_name = module_path.split(":", maxsplit=1)
        module = importlib.import_module(module_name)
        plugin_class = getattr(module, class_name)
        plugin = plugin_class()
        if not isinstance(plugin, PluginBase):
            raise TypeError("Plugin deve herdar PluginBase")
        return plugin

    @classmethod
    def execute(cls, *, module_path: str, task: str, payload: dict, context: dict) -> PluginExecutionResult:
        try:
            plugin = cls.load(module_path)
            result = plugin.run(task=task, payload=payload, context=context)
            return PluginExecutionResult(success=True, result=result)
        except Exception as exc:
            return PluginExecutionResult(success=False, result={}, error=str(exc))
