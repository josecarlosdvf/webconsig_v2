import json
import logging
import time

from app.core.redis_client import redis_client
from app.events.publisher import EventPublisher

logger = logging.getLogger("events.worker")


def run_worker() -> None:
    group = "webconsig-workers"
    consumer = "worker-1"
    stream = EventPublisher.stream_name

    try:
        redis_client.xgroup_create(stream, group, id="0", mkstream=True)
    except Exception:
        pass

    logger.info("worker_started", extra={"area": "eventos"})
    while True:
        entries = redis_client.xreadgroup(group, consumer, {stream: ">"}, count=10, block=5000)
        if not entries:
            continue
        for _, messages in entries:
            for message_id, payload in messages:
                try:
                    event_name = payload.get("event")
                    body = json.loads(payload.get("payload", "{}"))
                    logger.debug(
                        "event_consumed",
                        extra={"area": "eventos", "event": event_name, "payload": str(body)[:1500]},
                    )
                    redis_client.xack(stream, group, message_id)
                except Exception:
                    logger.exception("worker_event_error", extra={"area": "eventos"})
        time.sleep(0.1)
