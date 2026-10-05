import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
)

from privacy_engine.infrastructure.database.session import (
    create_database_engine,
)

TEST_DATABASE_URL = (
    "postgresql+asyncpg://"
    "privacy_user:privacy_password"
    "@localhost:5432/privacy_engine_test"
)


@pytest_asyncio.fixture
async def database_engine() -> AsyncEngine:
    engine = create_database_engine(
        TEST_DATABASE_URL
    )

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(
    database_engine: AsyncEngine,
) -> AsyncSession:
    async with database_engine.connect() as connection:
        await connection.execute(
            text(
                "TRUNCATE TABLE anonymization_mapping "
                "RESTART IDENTITY"
            )
        )
        await connection.commit()

        transaction = await connection.begin()

        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        try:
            yield session
        finally:
            await session.close()

            if transaction.is_active:
                await transaction.rollback()