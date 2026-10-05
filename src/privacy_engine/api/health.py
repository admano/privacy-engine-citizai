from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from privacy_engine.api.dependencies import get_db_session

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def readiness(
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> dict[str, str]:
    await session.execute(text("SELECT 1"))

    return {"status": "ready"}