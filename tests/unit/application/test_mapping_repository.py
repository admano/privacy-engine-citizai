
from uuid import UUID, uuid4

import pytest

from privacy_engine.application.models import AnonymizationMapping
from privacy_engine.application.repositories import MappingRepository

document_id = uuid4()

class FakeMappingRepository:
    def __init__(self) -> None:
        self.document_id: UUID | None = None
        self.saved_mappings: tuple[AnonymizationMapping, ...] | None = None

    async def save(
        self,
        document_id: UUID,
        mappings: tuple[AnonymizationMapping, ...],
    ) -> None:
        self.document_id = document_id
        self.saved_mappings = mappings


async def persist_mappings(
    repository: MappingRepository,
    document_id: UUID,
    mappings: tuple[AnonymizationMapping, ...],
) -> None:
    await repository.save(
        document_id=document_id,
        mappings=mappings,
    )




@pytest.mark.asyncio
async def test_mapping_repository_accepts_structural_implementation() -> None:
    repository = FakeMappingRepository()

    document_id = uuid4()

    mappings = (
        AnonymizationMapping(
            entity_type="EMAIL",
            original_value="adam@example.com",
            replacement_value="[EMAIL_001]",
        ),
    )

    await persist_mappings(
        repository=repository,
        document_id=document_id,
        mappings=mappings,
    )