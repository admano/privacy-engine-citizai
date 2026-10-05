import pytest

from privacy_engine.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
)


@pytest.mark.asyncio
async def test_create_session_factory() -> None:
    engine = create_database_engine(
        "postgresql+asyncpg://"
        "user:password@localhost:5432/test_db"
    )

    try:
        session_factory = create_session_factory(engine)

        assert session_factory is not None
    finally:
        await engine.dispose()