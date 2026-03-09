import logging
import sys
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging() -> None:
    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    root.handlers = []

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(user_id)s %(area)s"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

    for noisy in ("uvicorn.access",):
        logging.getLogger(noisy).setLevel(logging.INFO)
