from privacy_engine.application.language import (
    LanguageDetection,
    LanguageResolver,
)


class RecordingDetector:
    def __init__(self) -> None:
        self.called = False

    def detect(
        self,
        text: str,
    ) -> LanguageDetection:
        self.called = True

        return LanguageDetection(
            language="de",
            confidence=0.95,
        )


def test_language_is_detected_when_not_given() -> None:
    detector = RecordingDetector()
    resolver = LanguageResolver(
        detector=detector,
    )

    result = resolver.resolve(
        text="Hallo zusammen",
        requested_language=None,
    )

    assert result.language == "de"
    assert result.confidence == 0.95
    assert detector.called is True