import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from privacy_engine.application.exceptions import (
    DatabaseUnavailableError,
    InvalidInputError,
)

logger = logging.getLogger("privacy_engine.api")


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(InvalidInputError)
    async def invalid_input_handler(
        request: Request,
        exc: InvalidInputError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": str(exc),
            },
        )

    @app.exception_handler(DatabaseUnavailableError)
    async def database_unavailable_handler(
        request: Request,
        exc: DatabaseUnavailableError,
    ) -> JSONResponse:
        logger.error("database operation failed")

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": "Database temporarily unavailable",
            },
        )
