from uuid import UUID

import pytest

from privacy_engine.application.anonymization import TokenAnonymizer
from privacy_engine.application.anonymize_and_persist_text import (
    AnonymizeAndPersistText,
)
from privacy_engine.application.anonymize_text import AnonymizeText
from privacy_engine.application.entity_resolution import (
    EntityResolver,
)
from privacy_engine.application.language import LanguageResolver
from privacy_engine.application.models import AnonymizationMapping
from privacy_engine.domain.entities import PIIEntity
from tests.unit.application.test_anonymize_text import FixedLanguageDetector


class FakePIIProvider:
    def detect(self, text: str, language: str) -> list[PIIEntity]:
        email = "adam@example.com"
        start = text.index(email)

        return [
            PIIEntity(
                entity_type="EMAIL",
                value=email,
                start=start,
                end=start + len(email),
            )
        ]

class RecordingMappingRepository:
    def __init__(self) -> None:
        self.save_called = False
        self.document_id: UUID | None = None
        self.saved_mappings: tuple[AnonymizationMapping, ...] | None = None

    async def save(
        self,
        document_id: UUID,
        mappings: tuple[AnonymizationMapping, ...],
    ) -> None:
        self.save_called = True
        self.document_id = document_id
        self.saved_mappings = mappings

class EmptyPIIProvider:
    def detect(self, text: str, language: str) -> list[PIIEntity]:
        return []




@pytest.mark.asyncio
async def test_anonymize_and_persist_saves_generated_mappings() -> None:
    repository = RecordingMappingRepository()

    anonymize_text = AnonymizeText(
        provider=FakePIIProvider(),
        anonymizer=TokenAnonymizer(),
        entity_resolver=EntityResolver(),
        language_resolver=LanguageResolver(
            detector=FixedLanguageDetector(),
        ),
    )

    use_case = AnonymizeAndPersistText(
        anonymize_text=anonymize_text,
        repository=repository,
    )

    result = await use_case.execute(
        "Contact me at adam@example.com"
    )

    assert result.safe_text == "Contact me at [EMAIL_001]"
    assert result.entity_count == 1

    assert repository.saved_mappings is not None
    assert len(repository.saved_mappings) == 1

    mapping = repository.saved_mappings[0]

    assert mapping.original_value == "adam@example.com"
    assert mapping.replacement_value == "[EMAIL_001]"

@pytest.mark.asyncio
async def test_anonymize_and_persist_returns_anonymization_result() -> None:
    repository = RecordingMappingRepository()

    anonymize_text = AnonymizeText(
        provider=FakePIIProvider(),
        anonymizer=TokenAnonymizer(),
        entity_resolver=EntityResolver(),
        language_resolver=LanguageResolver(
            detector=FixedLanguageDetector(),
        ),
    )


    use_case = AnonymizeAndPersistText(
        anonymize_text=anonymize_text,
        repository=repository,
    )

    result = await use_case.execute(
        "Contact me at adam@example.com"
    )

    assert result.safe_text == "Contact me at [EMAIL_001]"
    assert result.entity_count == 1
    assert len(result.entities) == 1
    assert len(result.mappings) == 1

@pytest.mark.asyncio
async def test_anonymize_and_persist_does_not_save_when_no_mappings_exist() -> None:
    repository = RecordingMappingRepository()

    anonymize_text = AnonymizeText(
        provider=EmptyPIIProvider(),
        anonymizer=TokenAnonymizer(),
        entity_resolver=EntityResolver(),
        language_resolver=LanguageResolver(
            detector=FixedLanguageDetector(),
        ),
    )

    use_case = AnonymizeAndPersistText(
        anonymize_text=anonymize_text,
        repository=repository,
    )

    result = await use_case.execute(
        "Nothing sensitive here."
    )

    assert result.safe_text == "Nothing sensitive here."
    assert result.entity_count == 0

    assert repository.save_called is False