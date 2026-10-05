from privacy_engine.application.anonymization import TokenAnonymizer
from privacy_engine.application.anonymize_text import AnonymizeText
from privacy_engine.application.entity_resolution import EntityResolver
from privacy_engine.application.language import (
    LanguageDetection,
    LanguageResolver,
)
from privacy_engine.application.models import AnonymizerResult
from privacy_engine.domain.entities import PIIEntity


class FixedLanguageDetector:
    def detect(
        self,
        text: str,
    ) -> LanguageDetection:
        return LanguageDetection(
            language="en",
            confidence=1.0,
        )

language_resolver = LanguageResolver(
    detector=FixedLanguageDetector(),
)
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


class EmptyPIIProvider:
    def detect(self, text: str, language: str) -> list[PIIEntity]:
        return []




class RecordingAnonymizer:
    def __init__(self) -> None:
        self.received_text: str | None = None
        self.received_entities: list[PIIEntity] | None = None

    def anonymize(
        self,
        text: str,
        entities: list[PIIEntity],
    ) -> AnonymizerResult:
        self.received_text = text
        self.received_entities = entities

        return AnonymizerResult(
            safe_text="[SAFE]",
            mappings=(),
        )


def test_anonymize_text_returns_safe_text_and_entity_count() -> None:
    use_case = AnonymizeText(
        provider=FakePIIProvider(),
        anonymizer=TokenAnonymizer(),
        entity_resolver=EntityResolver(),
        language_resolver=language_resolver,
    )

    result = use_case.execute(
        "Contact me at adam@example.com"
    )

    assert result.safe_text == "Contact me at [EMAIL_001]"
    assert result.entity_count == 1


def test_anonymize_text_returns_original_text_when_no_pii_exists() -> None:
    text = "Nothing sensitive here."

    use_case = AnonymizeText(
        provider=EmptyPIIProvider(),
        anonymizer=TokenAnonymizer(),
        entity_resolver=EntityResolver(),
        language_resolver=language_resolver,
    )

    result = use_case.execute(text)

    assert result.safe_text == text
    assert result.entity_count == 0


def test_use_case_passes_detected_entities_to_anonymizer() -> None:
    anonymizer = RecordingAnonymizer()

    use_case = AnonymizeText(
        provider=FakePIIProvider(),
        anonymizer=anonymizer,
        entity_resolver=EntityResolver(),
        language_resolver=LanguageResolver(
            detector=FixedLanguageDetector(),
        ),
    )

    text = "Contact me at adam@example.com"

    result = use_case.execute(text)

    assert anonymizer.received_text == text
    assert anonymizer.received_entities is not None
    assert len(anonymizer.received_entities) == 1

    assert result.safe_text == "[SAFE]"