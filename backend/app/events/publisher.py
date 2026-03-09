import json
import logging

from app.core.config import settings
from app.core.redis_client import redis_client

logger = logging.getLogger("events")


class EventPublisher:
    stream_name = "webconsig:events"

    @classmethod
    def publish(cls, event_name: str, payload: dict) -> None:
        message = {"event": event_name, "payload": json.dumps(payload, default=str)}
        try:
            redis_client.xadd(cls.stream_name, message, maxlen=50000, approximate=True)
            logger.debug("event_published", extra={"area": "eventos", "event": event_name})
        except Exception:
            logger.exception("redis_stream_publish_error", extra={"area": "eventos", "event": event_name})
        if settings.use_rabbitmq:
            cls._publish_rabbitmq(event_name, payload)

    @classmethod
    def _publish_rabbitmq(cls, event_name: str, payload: dict) -> None:
        try:
            import pika

            parameters = pika.URLParameters(settings.rabbitmq_url)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.exchange_declare(exchange=settings.rabbitmq_exchange, exchange_type="topic", durable=True)
            channel.basic_publish(
                exchange=settings.rabbitmq_exchange,
                routing_key=event_name,
                body=json.dumps(payload, default=str),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            connection.close()
        except Exception:
            logger.exception("rabbitmq_publish_error", extra={"area": "eventos", "event": event_name})
