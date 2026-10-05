from privacy_engine.application.anonymization import TokenAnonymizer
from privacy_engine.application.anonymize_markdown import (
    AnonymizeMarkdown,
)
from privacy_engine.application.entity_resolution import (
    EntityResolver,
)
from privacy_engine.application.language import (
    LanguageDetection,
    LanguageResolver,
)
from privacy_engine.application.markdown_models import MarkdownDocument
from privacy_engine.domain.entities import PIIEntity
from privacy_engine.infrastructure.markdown.regex_markdown_processor import (
    RegexMarkdownProcessor,
)


class FixedLanguageDetector:
    def detect(
        self,
        text: str,
    ) -> LanguageDetection:
        return LanguageDetection(
            language="en",
            confidence=1.0,
        )


class NamePIIProvider:
    """Detects every occurrence of the literal "John Smith"."""

    def detect(
        self,
        text: str,
        language: str,
    ) -> list[PIIEntity]:
        entities = []
        needle = "John Smith"
        cursor = 0

        while True:
            index = text.find(needle, cursor)

            if index == -1:
                break

            entities.append(
                PIIEntity(
                    entity_type="PERSON",
                    value=needle,
                    start=index,
                    end=index + len(needle),
                )
            )

            cursor = index + len(needle)

        return entities


def _build_use_case() -> AnonymizeMarkdown:
    return AnonymizeMarkdown(
        provider=NamePIIProvider(),
        anonymizer=TokenAnonymizer(),
        entity_resolver=EntityResolver(),
        language_resolver=LanguageResolver(
            detector=FixedLanguageDetector(),
        ),
        markdown_processor=RegexMarkdownProcessor(),
    )


def test_markdown_anonymization_preserves_structure_end_to_end() -> None:
    use_case = _build_use_case()

    document = MarkdownDocument(
        filename="customer.md",
        content=(
            "# Customer\n\n"
            "Name: John Smith\n\n"
            "```\n"
            "John Smith\n"
            "```\n\n"
            "[Profile](https://example.com/john-smith)"
        ),
    )

    result = use_case.execute(document)

    assert result.safe_markdown == (
        "# Customer\n\n"
        "Name: [PERSON_001]\n\n"
        "```\n"
        "John Smith\n"
        "```\n\n"
        "[Profile](https://example.com/john-smith)"
    )
    # Only the paragraph occurrence is detected: the code block is
    # never handed to the PII provider.
    assert result.entity_count == 1
    assert result.mappings[0].original_value == "John Smith"


def test_markdown_anonymization_leaves_link_destination_untouched() -> (
    None
):
    use_case = _build_use_case()

    document = MarkdownDocument(
        filename="notes.md",
        content="[Contact John Smith](https://example.com/john-smith)",
    )

    result = use_case.execute(document)

    assert result.safe_markdown == (
        "[Contact [PERSON_001]](https://example.com/john-smith)"
    )
