from typing import Protocol

from privacy_engine.domain.entities import PIIEntity


class _AnalyzerResult(Protocol):
    entity_type: str
    start: int
    end: int
    score: float


class _Analyzer(Protocol):
    def analyze(
        self,
        text: str,
        language: str,
    ) -> list[_AnalyzerResult]: ...


class PresidioPIIProvider:
    """Inactive legacy adapter for a separately supplied Presidio analyzer.

    The application does not construct this provider and does not depend on
    Presidio. Keeping the interface structural lets this module remain
    importable when Presidio is absent.
    """

    def __init__(
        self,
        analyzer: _Analyzer,
    ) -> None:
        self._analyzer = analyzer

    def detect(
        self,
        text: str,
        language: str,
    ) -> list[PIIEntity]:
        if not text:
            return []

        results = self._analyzer.analyze(
            text=text,
            language=language,
        )

        return [
            PIIEntity(
                entity_type=result.entity_type,
                value=text[
                    result.start:result.end
                ],
                start=result.start,
                end=result.end,
                score=result.score,
            )
            for result in results
        ]
