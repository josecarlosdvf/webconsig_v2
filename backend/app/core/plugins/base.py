from __future__ import annotations

from abc import ABC, abstractmethod


class PluginBase(ABC):
    @property
    @abstractmethod
    def slug(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def version(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def run(self, *, task: str, payload: dict, context: dict) -> dict:
        raise NotImplementedError
