import re
from collections.abc import Callable

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


class FixedLanguageDetector:
    def __init__(self) -> None:
        self.received_text: str | None = None

    def detect(
        self,
        text: str,
    ) -> LanguageDetection:
        self.received_text = text

        return LanguageDetection(
            language="en",
            confidence=1.0,
        )


class PassthroughMarkdownProcessor:
    """Calls transform on the whole markdown as a single fragment."""

    def __init__(self) -> None:
        self.received_markdown: str | None = None

    def transform_text(
        self,
        markdown: str,
        transform: Callable[[str], str],
    ) -> str:
        self.received_markdown = markdown

        return transform(markdown)


class TwoFragmentMarkdownProcessor:
    """Splits markdown into two halves and transforms each separately."""

    def transform_text(
        self,
        markdown: str,
        transform: Callable[[str], str],
    ) -> str:
        midpoint = len(markdown) // 2

        return transform(markdown[:midpoint]) + transform(
            markdown[midpoint:]
        )


class EmailPIIProvider:
    def detect(
        self,
        text: str,
        language: str,
    ) -> list[PIIEntity]:
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


class RegexEmailPIIProvider:
    _PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

    def detect(
        self,
        text: str,
        language: str,
    ) -> list[PIIEntity]:
        return [
            PIIEntity(
                entity_type="EMAIL",
                value=match.group(0),
                start=match.start(),
                end=match.end(),
            )
            for match in self._PATTERN.finditer(text)
        ]


class EmptyPIIProvider:
    def detect(
        self,
        text: str,
        language: str,
    ) -> list[PIIEntity]:
        return []


def _build_use_case(
    provider,
    markdown_processor,
) -> AnonymizeMarkdown:
    return AnonymizeMarkdown(
        provider=provider,
        anonymizer=TokenAnonymizer(),
        entity_resolver=EntityResolver(),
        language_resolver=LanguageResolver(
            detector=FixedLanguageDetector(),
        ),
        markdown_processor=markdown_processor,
    )


def test_anonymize_markdown_returns_safe_markdown_and_entity_count() -> (
    None
):
    use_case = _build_use_case(
        EmailPIIProvider(),
        PassthroughMarkdownProcessor(),
    )

    document = MarkdownDocument(
        filename="notes.md",
        content="Contact me at adam@example.com",
    )

    result = use_case.execute(document)

    assert result.safe_markdown == "Contact me at [EMAIL_001]"
    assert result.entity_count == 1
    assert result.entities[0].value == "adam@example.com"
    assert result.mappings[0].replacement_value == "[EMAIL_001]"


def test_anonymize_markdown_preserves_filename_and_language() -> None:
    use_case = _build_use_case(
        EmptyPIIProvider(),
        PassthroughMarkdownProcessor(),
    )

    document = MarkdownDocument(
        filename="report.md",
        content="Nothing sensitive here.",
    )

    result = use_case.execute(document)

    assert result.filename == "report.md"
    assert result.language == "en"


def test_anonymize_markdown_returns_original_text_when_no_pii_exists() -> (
    None
):
    use_case = _build_use_case(
        EmptyPIIProvider(),
        PassthroughMarkdownProcessor(),
    )

    document = MarkdownDocument(
        filename="notes.md",
        content="Nothing sensitive here.",
    )

    result = use_case.execute(document)

    assert result.safe_markdown == "Nothing sensitive here."
    assert result.entity_count == 0
    assert result.entities == ()
    assert result.mappings == ()


def test_anonymize_markdown_is_safe_for_ai_when_no_entities_detected() -> (
    None
):
    use_case = _build_use_case(
        EmptyPIIProvider(),
        PassthroughMarkdownProcessor(),
    )

    document = MarkdownDocument(
        filename="notes.md",
        content="Nothing sensitive here.",
    )

    result = use_case.execute(document)

    assert result.is_safe_for_ai is True


def test_anonymize_markdown_is_not_safe_for_ai_when_entities_detected() -> (
    None
):
    use_case = _build_use_case(
        EmailPIIProvider(),
        PassthroughMarkdownProcessor(),
    )

    document = MarkdownDocument(
        filename="notes.md",
        content="Contact me at adam@example.com",
    )

    result = use_case.execute(document)

    assert result.is_safe_for_ai is False


def test_anonymize_markdown_generates_a_document_id() -> None:
    use_case = _build_use_case(
        EmptyPIIProvider(),
        PassthroughMarkdownProcessor(),
    )

    document = MarkdownDocument(
        filename="notes.md",
        content="Nothing sensitive here.",
    )

    first = use_case.execute(document)
    second = use_case.execute(document)

    assert first.document_id != second.document_id


def test_anonymize_markdown_delegates_fragmenting_to_markdown_processor() -> (
    None
):
    processor = PassthroughMarkdownProcessor()

    use_case = _build_use_case(
        EmptyPIIProvider(),
        processor,
    )

    document = MarkdownDocument(
        filename="notes.md",
        content="# Heading\n\nBody text",
    )

    use_case.execute(document)

    assert processor.received_markdown == "# Heading\n\nBody text"


def test_anonymize_markdown_aggregates_entities_across_fragments() -> None:
    use_case = _build_use_case(
        RegexEmailPIIProvider(),
        TwoFragmentMarkdownProcessor(),
    )

    # One distinct email in each half of the document.
    content = "alice@example.com" + (" " * 20) + "bob@example.com"
    document = MarkdownDocument(
        filename="notes.md",
        content=content,
    )

    result = use_case.execute(document)

    assert result.entity_count == 2
    assert len(result.mappings) == 2

    original_values = {
        mapping.original_value for mapping in result.mappings
    }

    assert original_values == {"alice@example.com", "bob@example.com"}


def test_anonymize_markdown_uses_requested_language_over_detection() -> (
    None
):
    detector = FixedLanguageDetector()

    use_case = AnonymizeMarkdown(
        provider=EmptyPIIProvider(),
        anonymizer=TokenAnonymizer(),
        entity_resolver=EntityResolver(),
        language_resolver=LanguageResolver(detector=detector),
        markdown_processor=PassthroughMarkdownProcessor(),
    )

    document = MarkdownDocument(
        filename="notes.md",
        content="Bonjour le monde",
    )

    result = use_case.execute(document, language="fr")

    assert result.language == "fr"
    assert detector.received_text is None
