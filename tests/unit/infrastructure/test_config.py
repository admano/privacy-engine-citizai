from privacy_engine.infrastructure.config import Settings


def test_settings_reads_database_url() -> None:
    settings = Settings(
        database_url=(
            "postgresql+asyncpg://"
            "user:password@localhost:5432/test_db"
        )
    )

    assert settings.database_url.endswith("/test_db")
