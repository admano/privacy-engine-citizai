from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from privacy_engine.application.exceptions import (
    DatabaseUnavailableError,
)
from privacy_engine.application.models import AnonymizationMapping
from privacy_engine.infrastructure.database.models import (
    AnonymizationMappingModel,
)


class SQLAlchemyMappingRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def save(
        self,
        document_id: UUID,
        mappings: tuple[AnonymizationMapping, ...],
    ) -> None:
        if not mappings:
            return

        models = [
            AnonymizationMappingModel(
                document_id=document_id,
                entity_type=mapping.entity_type,
                original_value=mapping.original_value,
                replacement_value=mapping.replacement_value,
            )
            for mapping in mappings
        ]

        try:
            self._session.add_all(models)
            await self._session.flush()

        except SQLAlchemyError as exc:
            raise DatabaseUnavailableError(
                "Database persistence failed"
            ) from exc