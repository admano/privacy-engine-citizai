from typing import Protocol

from privacy_engine.application.models import AnonymizerResult
from privacy_engine.domain.entities import PIIEntity


class Anonymizer(Protocol):
    def anonymize(
        self,
        text: str,
        entities: list[PIIEntity],
    ) -> AnonymizerResult:
        ...