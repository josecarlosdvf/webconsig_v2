from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime
from threading import Lock


_EVENTS: deque[dict] = deque(maxlen=2000)
_SUBSCRIBERS: set[asyncio.Queue] = set()
_LOCK = Lock()


def publish_event(*, event_type: str, payload: dict) -> None:
    event = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload,
    }

    with _LOCK:
        _EVENTS.append(event)
        subscribers = list(_SUBSCRIBERS)

    for queue in subscribers:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            pass


def list_recent_events(*, limit: int = 100, event_type: str | None = None) -> list[dict]:
    with _LOCK:
        items = list(_EVENTS)

    if event_type:
        items = [item for item in items if item.get("event_type") == event_type]

    return list(reversed(items[-limit:]))


async def subscribe(queue_size: int = 200) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
    with _LOCK:
        _SUBSCRIBERS.add(queue)
    return queue


async def unsubscribe(queue: asyncio.Queue) -> None:
    with _LOCK:
        _SUBSCRIBERS.discard(queue)
