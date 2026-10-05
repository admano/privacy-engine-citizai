from privacy_engine.application.anonymization import TokenAnonymizer
from privacy_engine.application.anonymize_text import AnonymizeText
from privacy_engine.application.entity_resolution import (
    EntityResolver,
)
from privacy_engine.application.language import (
    LanguageDetection,
    LanguageResolver,
)
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


def test_duplicate_email_detection_does_not_corrupt_safe_text() -> None:
    class DuplicateEmailProvider:
        def detect(
            self,
            text: str,
            language: str,
        ) -> list[PIIEntity]:
            return [
                PIIEntity(
                    entity_type="EMAIL",
                    value="adam@example.com",
                    start=7,
                    end=23,
                    score=0.95,
                ),
                PIIEntity(
                    entity_type="EMAIL_ADDRESS",
                    value="adam@example.com",
                    start=7,
                    end=23,
                    score=0.85,
                ),
            ]

    use_case = AnonymizeText(
        provider=DuplicateEmailProvider(),
        anonymizer=TokenAnonymizer(),
        entity_resolver=EntityResolver(),
        language_resolver=LanguageResolver(
            detector=FixedLanguageDetector(),
        ),
    )

    result = use_case.execute(
        text="Email: adam@example.com",
        language="en",
    )

    assert result.safe_text == "Email: [EMAIL_001]"
    assert result.entity_count == 1