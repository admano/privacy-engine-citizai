from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from privacy_engine.application.models import AnonymizationMapping
from privacy_engine.infrastructure.database.models import (
    AnonymizationMappingModel,
)
from privacy_engine.infrastructure.database.repositories import (
    SQLAlchemyMappingRepository,
)

document_id = uuid4()

@pytest.mark.asyncio
async def test_mapping_repository_persists_mapping_in_postgresql(
    db_session: AsyncSession,
) -> None:
    repository = SQLAlchemyMappingRepository(
        session=db_session,
    )

    mapping = AnonymizationMapping(
        entity_type="EMAIL",
        original_value="adam@example.com",
        replacement_value="[EMAIL_001]",
    )

    await repository.save(
        document_id=document_id,
        mappings=(mapping,),
    )

    result = await db_session.execute(
        select(AnonymizationMappingModel)
    )

    persisted = result.scalars().all()

    assert len(persisted) == 1
    assert persisted[0].entity_type == "EMAIL"
    assert persisted[0].original_value == "adam@example.com"
    assert persisted[0].replacement_value == "[EMAIL_001]"
    assert persisted[0].document_id == document_id

@pytest.mark.asyncio
async def test_mapping_repository_persists_multiple_mappings(
    db_session: AsyncSession,
) -> None:
    repository = SQLAlchemyMappingRepository(
        session=db_session,
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

    result = await db_session.execute(
        select(AnonymizationMappingModel)
    )

    persisted = result.scalars().all()

    assert len(persisted) == 2

    assert all(
        row.document_id == document_id
        for row in persisted
    )