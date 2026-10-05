import pytest

from privacy_engine.application.exceptions import InvalidInputError
from privacy_engine.infrastructure.language.fasttext_detector import (
    FastTextLanguageDetector,
)


class FakeDetector:
    def __init__(self, candidates: list[dict[str, float | str]]) -> None:
        self._candidates = candidates
        self.calls: list[tuple[str, int]] = []

    def detect(self, text: str, k: int) -> list[dict[str, float | str]]:
        self.calls.append((text, k))
        return self._candidates


def test_returns_supported_language_and_confidence() -> None:
    client = FakeDetector([{"lang": "de", "score": 0.91}])

    result = FastTextLanguageDetector(client).detect("Hallo zusammen")

    assert result.language == "de"
    assert result.confidence == 0.91
    assert client.calls == [("Hallo zusammen", 1)]


@pytest.mark.parametrize(
    ("text", "expected_language"),
    [
        ("Meine Telefonnummer ist vertraulich.", "de"),
        ("Mon numéro de téléphone est confidentiel.", "fr"),
        ("Il mio numero di telefono è riservato.", "it"),
        ("My phone number is confidential.", "en"),
    ],
)
def test_detects_supported_languages(
    text: str,
    expected_language: str,
) -> None:
    result = FastTextLanguageDetector().detect(text)

    assert result.language == expected_language
    assert result.confidence >= 0.5


@pytest.mark.parametrize(
    "candidates",
    [
        [],
        [{"lang": "es", "score": 0.99}],
        [{"lang": "en", "score": 0.49}],
    ],
)
def test_rejects_unusable_detection(
    candidates: list[dict[str, float | str]],
) -> None:
    detector = FastTextLanguageDetector(
        FakeDetector(candidates),
        min_confidence=0.5,
    )

    with pytest.raises(InvalidInputError):
        detector.detect("text")
