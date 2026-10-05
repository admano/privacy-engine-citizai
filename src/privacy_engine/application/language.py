from dataclasses import dataclass
from typing import Protocol

SUPPORTED_LANGUAGES = frozenset(
    {
        "de",
        "fr",
        "it",
        "en",
    }
)


@dataclass(frozen=True, slots=True)
class LanguageDetection:
    language: str
    confidence: float


class LanguageDetector(Protocol):
    def detect(
        self,
        text: str,
    ) -> LanguageDetection:
        ...


class LanguageResolver:
    def __init__(
        self,
        detector: LanguageDetector,
    ) -> None:
        self._detector = detector

    def resolve(
        self,
        text: str,
        requested_language: str | None,
    ) -> LanguageDetection:
        if requested_language is not None:
            if requested_language not in SUPPORTED_LANGUAGES:
                raise ValueError(
                    f"Unsupported language: {requested_language}"
                )

            return LanguageDetection(
                language=requested_language,
                confidence=1.0,
            )

        return self._detector.detect(text)