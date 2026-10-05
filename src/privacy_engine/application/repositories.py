from typing import Protocol
from uuid import UUID

from privacy_engine.application.models import AnonymizationMapping


class MappingRepository(Protocol):
    async def save(
        self,
        document_id: UUID,
        mappings: tuple[AnonymizationMapping, ...],
    ) -> None:
        ...