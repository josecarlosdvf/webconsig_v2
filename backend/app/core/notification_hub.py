from __future__ import annotations

import asyncio
from collections import defaultdict
from threading import Lock


_SUBSCRIBERS: dict[str, set[asyncio.Queue]] = defaultdict(set)
_LOCK = Lock()


def publish_notification(*, recipient: str, payload: dict) -> None:
    with _LOCK:
        recipients = list(_SUBSCRIBERS.get(recipient, set()))

    for queue in recipients:
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            pass


async def subscribe_recipient(*, recipient: str, queue_size: int = 200) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
    with _LOCK:
        _SUBSCRIBERS[recipient].add(queue)
    return queue


async def unsubscribe_recipient(*, recipient: str, queue: asyncio.Queue) -> None:
    with _LOCK:
        if recipient in _SUBSCRIBERS:
            _SUBSCRIBERS[recipient].discard(queue)
            if not _SUBSCRIBERS[recipient]:
                del _SUBSCRIBERS[recipient]
