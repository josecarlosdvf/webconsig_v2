from collections import deque
from datetime import datetime
from threading import Lock


_EVENTS: deque[dict] = deque(maxlen=5000)
_LOCK = Lock()


def push_debug_event(
    *,
    source: str,
    level: str,
    message: str,
    context: dict | None = None,
    request_id: str | None = None,
    actor: str | None = None,
    path: str | None = None,
) -> None:
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source,
        "level": level.upper(),
        "message": message,
        "context": context or {},
        "request_id": request_id,
        "actor": actor,
        "path": path,
    }
    with _LOCK:
        _EVENTS.append(event)


def list_debug_events(*, limit: int = 200, source: str | None = None, level: str | None = None) -> list[dict]:
    with _LOCK:
        items = list(_EVENTS)

    if source:
        items = [event for event in items if event.get("source") == source]
    if level:
        items = [event for event in items if event.get("level") == level.upper()]

    return list(reversed(items[-limit:]))


def debug_summary() -> dict:
    with _LOCK:
        items = list(_EVENTS)

    by_source: dict[str, int] = {}
    by_level: dict[str, int] = {}
    for event in items:
        source = event.get("source", "unknown")
        level = event.get("level", "INFO")
        by_source[source] = by_source.get(source, 0) + 1
        by_level[level] = by_level.get(level, 0) + 1

    return {"total": len(items), "by_source": by_source, "by_level": by_level}
