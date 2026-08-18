import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone


request_id_context = ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None) or request_id_context.get(),
        }

        for key in [
            "project_id",
            "task_id",
            "agent",
            "event",
            "duration_ms",
            "status",
            "path",
            "method",
            "status_code",
            "user_id",
            "run_id",
            "benchmark_run_id",
            "error",
        ]:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging():
    root_logger = logging.getLogger()
    if getattr(root_logger, "_structured_logging_configured", False):
        return

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)
    root_logger._structured_logging_configured = True


def get_logger(name):
    configure_logging()
    return logging.getLogger(name)


def set_request_id(request_id):
    return request_id_context.set(request_id)


def reset_request_id(token):
    request_id_context.reset(token)
