from __future__ import annotations

import json
from datetime import datetime
from typing import cast

from redis import Redis

from app.core.config import settings
from app.core.plugins.base import PluginBase


class ChatHubPlugin(PluginBase):
    @property
    def slug(self) -> str:
        return "chat-hub"

    @property
    def name(self) -> str:
        return "Chat Hub Plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @staticmethod
    def _redis() -> Redis:
        return Redis.from_url(settings.redis_url, decode_responses=True)

    @staticmethod
    def _room_key(room: str) -> str:
        return f"plugin:chat:room:{room}"

    def run(self, *, task: str, payload: dict, context: dict) -> dict:
        redis_client = self._redis()

        if task == "send_message":
            room = str(payload.get("room") or "geral").strip().lower()
            message = str(payload.get("message") or "").strip()
            if not message:
                raise ValueError("Mensagem obrigatória")

            item = {
                "room": room,
                "message": message,
                "actor": context.get("actor", "anonymous"),
                "created_at": datetime.utcnow().isoformat(),
            }
            key = self._room_key(room)
            redis_client.lpush(key, json.dumps(item, ensure_ascii=False))
            redis_client.ltrim(key, 0, 499)
            return {"sent": True, "item": item}

        if task == "list_messages":
            room = str(payload.get("room") or "geral").strip().lower()
            limit = int(payload.get("limit") or 50)
            limit = 1 if limit < 1 else 200 if limit > 200 else limit
            rows = cast(list[str], redis_client.lrange(self._room_key(room), 0, limit - 1))
            items = [json.loads(row) for row in rows]
            return {"room": room, "items": items, "total": len(items)}

        if task == "list_rooms":
            keys = cast(list[str], redis_client.keys("plugin:chat:room:*"))
            rooms = sorted(key.split(":")[-1] for key in keys)
            return {"items": rooms, "total": len(rooms)}

        raise ValueError(f"Task não suportada: {task}")
