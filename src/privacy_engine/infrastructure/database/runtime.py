from dataclasses import dataclass

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from privacy_engine.infrastructure.config import Settings
from privacy_engine.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
)


@dataclass(frozen=True, slots=True)
class DatabaseRuntime:
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]


def create_database_runtime(
    settings: Settings,
) -> DatabaseRuntime:
    engine = create_database_engine(
        settings.database_url,
    )

    session_factory = create_session_factory(
        engine,
    )

    return DatabaseRuntime(
        engine=engine,
        session_factory=session_factory,
    )