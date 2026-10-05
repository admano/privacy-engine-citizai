from typing import Protocol, TypedDict

from privacy_engine.application.exceptions import InvalidInputError
from privacy_engine.application.language import (
    SUPPORTED_LANGUAGES,
    LanguageDetection,
)


class _Candidate(TypedDict):
    lang: str
    score: float


class _FastTextClient(Protocol):
    def detect(self, text: str, k: int) -> list[_Candidate]: ...


class FastTextLanguageDetector:
    def __init__(
        self,
        client: _FastTextClient | None = None,
        min_confidence: float = 0.7,
    ) -> None:
        self._client = client or self._build_client()
        self._min_confidence = min_confidence

    @staticmethod
    def _build_client() -> _FastTextClient:
        from fast_langdetect import LangDetectConfig, LangDetector

        return LangDetector(LangDetectConfig(model="lite"))

    def detect(self, text: str) -> LanguageDetection:
        if not text.strip():
            raise InvalidInputError("Unable to detect input language")

        candidates = self._client.detect(text, k=1)

        if not candidates:
            raise InvalidInputError("Unable to detect input language")

        candidate = candidates[0]
        language = candidate["lang"]
        confidence = float(candidate["score"])

        if language not in SUPPORTED_LANGUAGES:
            raise InvalidInputError("Unable to detect input language")

        if confidence < self._min_confidence:
            raise InvalidInputError("Unable to detect input language")

        return LanguageDetection(
            language=language,
            confidence=confidence,
        )
