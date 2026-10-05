import json
import logging

from privacy_engine.infrastructure.logging_context import (
    get_request_id,
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }

        if hasattr(record, "method"):
            payload["method"] = record.method

        if hasattr(record, "path"):
            payload["path"] = record.path

        if hasattr(record, "status_code"):
            payload["status_code"] = record.status_code

        if record.exc_info:
            payload["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(payload)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)