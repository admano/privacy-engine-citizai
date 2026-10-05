from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from privacy_engine.api.error_handlers import (
    register_exception_handlers,
)
from privacy_engine.api.health import router as health_router
from privacy_engine.api.middleware import RequestContextMiddleware
from privacy_engine.api.routes import router as privacy_router
from privacy_engine.infrastructure.config import get_settings
from privacy_engine.infrastructure.database.runtime import (
    create_database_runtime,
)
from privacy_engine.infrastructure.logging import configure_logging

configure_logging()


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    settings = get_settings()
    database = create_database_runtime(settings)

    app.state.database = database

    try:
        yield
    finally:
        await database.engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Privacy Engine",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        RequestContextMiddleware,
    )

    register_exception_handlers(app)

    app.include_router(
        health_router,
        prefix="/api/v1",
    )

    app.include_router(
        privacy_router,
        prefix="/api/v1",
    )

    return app


app = create_app()