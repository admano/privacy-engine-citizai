from collections.abc import Callable
from uuid import UUID

import pytest

from privacy_engine.application.anonymization import TokenAnonymizer
from privacy_engine.application.anonymize_and_persist_markdown import (
    AnonymizeAndPersistMarkdown,
)
from privacy_engine.application.anonymize_markdown import (
    AnonymizeMarkdown,
)
from privacy_engine.application.entity_resolution import (
    EntityResolver,
)
from privacy_engine.application.language import LanguageResolver
from privacy_engine.application.markdown_models import MarkdownDocument
from privacy_engine.application.models import AnonymizationMapping
from privacy_engine.domain.entities import PIIEntity
from tests.unit.application.test_anonymize_text import (
    FixedLanguageDetector,
)


class PassthroughMarkdownProcessor:
    def transform_text(
        self,
        markdown: str,
        transform: Callable[[str], str],
    ) -> str:
        return transform(markdown)


class FakePIIProvider:
    def detect(self, text: str, language: str) -> list[PIIEntity]:
        email = "adam@example.com"

        if email not in text:
            return []

        start = text.index(email)

        return [
            PIIEntity(
                entity_type="EMAIL",
                value=email,
                start=start,
                end=start + len(email),
            )
        ]


class EmptyPIIProvider:
    def detect(self, text: str, language: str) -> list[PIIEntity]:
        return []


class RecordingMappingRepository:
    def __init__(self) -> None:
        self.save_called = False
        self.document_id: UUID | None = None
        self.saved_mappings: (
            tuple[AnonymizationMapping, ...] | None
        ) = None

    async def save(
        self,
        document_id: UUID,
        mappings: tuple[AnonymizationMapping, ...],
    ) -> None:
        self.save_called = True
        self.document_id = document_id
        self.saved_mappings = mappings


def _build_anonymize_markdown(provider) -> AnonymizeMarkdown:
    return AnonymizeMarkdown(
        provider=provider,
        anonymizer=TokenAnonymizer(),
        entity_resolver=EntityResolver(),
        language_resolver=LanguageResolver(
            detector=FixedLanguageDetector(),
        ),
        markdown_processor=PassthroughMarkdownProcessor(),
    )


@pytest.mark.asyncio
async def test_anonymize_and_persist_markdown_saves_generated_mappings() -> (
    None
):
    repository = RecordingMappingRepository()

    use_case = AnonymizeAndPersistMarkdown(
        anonymize_markdown=_build_anonymize_markdown(FakePIIProvider()),
        repository=repository,
    )

    document = MarkdownDocument(
        filename="notes.md",
        content="Contact me at adam@example.com",
    )

    result = await use_case.execute(document)

    assert result.safe_markdown == "Contact me at [EMAIL_001]"
    assert result.entity_count == 1

    assert repository.save_called is True
    assert repository.document_id == result.document_id
    assert repository.saved_mappings is not None
    assert len(repository.saved_mappings) == 1

    mapping = repository.saved_mappings[0]

    assert mapping.original_value == "adam@example.com"
    assert mapping.replacement_value == "[EMAIL_001]"


@pytest.mark.asyncio
async def test_anonymize_and_persist_markdown_returns_full_result() -> (
    None
):
    repository = RecordingMappingRepository()

    use_case = AnonymizeAndPersistMarkdown(
        anonymize_markdown=_build_anonymize_markdown(FakePIIProvider()),
        repository=repository,
    )

    document = MarkdownDocument(
        filename="notes.md",
        content="Contact me at adam@example.com",
    )

    result = await use_case.execute(document)

    assert result.filename == "notes.md"
    assert result.language == "en"
    assert len(result.entities) == 1
    assert len(result.mappings) == 1


@pytest.mark.asyncio
async def test_anonymize_and_persist_markdown_does_not_save_when_no_mappings_exist() -> (
    None
):
    repository = RecordingMappingRepository()

    use_case = AnonymizeAndPersistMarkdown(
        anonymize_markdown=_build_anonymize_markdown(EmptyPIIProvider()),
        repository=repository,
    )

    document = MarkdownDocument(
        filename="notes.md",
        content="Nothing sensitive here.",
    )

    result = await use_case.execute(document)

    assert result.safe_markdown == "Nothing sensitive here."
    assert result.entity_count == 0

    assert repository.save_called is False
