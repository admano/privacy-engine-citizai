import logging
import re
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from privacy_engine.infrastructure.logging_context import (
    reset_request_id,
    set_request_id,
)

logger = logging.getLogger("privacy_engine.api")

# Client-supplied request IDs are echoed into every log line and the
# response headers for the request, so only accept an opaque-token
# shape within a sane length instead of trusting arbitrary input.
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        client_request_id = request.headers.get("X-Request-ID")

        request_id = (
            client_request_id
            if client_request_id
            and _REQUEST_ID_PATTERN.fullmatch(client_request_id)
            else str(uuid4())
        )

        token = set_request_id(request_id)

        try:
            logger.info(
                "request started",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                },
            )

            response = await call_next(request)

            response.headers["X-Request-ID"] = request_id

            logger.info(
                "request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                },
            )

            return response

        finally:
            reset_request_id(token)