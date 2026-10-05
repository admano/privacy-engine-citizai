from uuid import uuid4

import pytest

from privacy_engine.application.models import AnonymizationMapping
from privacy_engine.infrastructure.database.repositories import (
    SQLAlchemyMappingRepository,
)

document_id = uuid4()

class FakeAsyncSession:
    def __init__(self) -> None:
        self.added_models = []
        self.flush_called = False

    def add_all(self, models) -> None:
        self.added_models.extend(models)

    async def flush(self) -> None:
        self.flush_called = True



@pytest.mark.asyncio
async def test_repository_persists_mapping_models() -> None:
    session = FakeAsyncSession()

    repository = SQLAlchemyMappingRepository(
        session=session,
    )

    document_id = uuid4()

    mappings = (
        AnonymizationMapping(
            entity_type="EMAIL",
            original_value="adam@example.com",
            replacement_value="[EMAIL_001]",
        ),
    )

    await repository.save(
        document_id=document_id,
        mappings=mappings,
    )

    assert len(session.added_models) == 1
    assert session.added_models[0].document_id == document_id
    assert session.flush_called is True

@pytest.mark.asyncio
async def test_repository_persists_multiple_mappings() -> None:
    session = FakeAsyncSession()

    repository = SQLAlchemyMappingRepository(
        session=session,
    )

    document_id = uuid4()

    mappings = (
        AnonymizationMapping(
            entity_type="PERSON",
            original_value="Adam",
            replacement_value="[PERSON_001]",
        ),
        AnonymizationMapping(
            entity_type="EMAIL",
            original_value="adam@example.com",
            replacement_value="[EMAIL_001]",
        ),
    )

    await repository.save(
        document_id=document_id,
        mappings=mappings,
    )

    assert len(session.added_models) == 2

    assert all(
        model.document_id == document_id
        for model in session.added_models
    )

    assert session.flush_called is True
    

@pytest.mark.asyncio
async def test_repository_does_nothing_for_empty_mappings() -> None:
    session = FakeAsyncSession()

    repository = SQLAlchemyMappingRepository(
        session=session,
    )

    await repository.save(
        document_id=uuid4(),
        mappings=(),
    )

    assert session.added_models == []
    assert session.flush_called is False