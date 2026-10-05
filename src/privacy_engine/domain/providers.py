from typing import Protocol

from privacy_engine.domain.entities import PIIEntity


class PIIProvider(Protocol):
    def detect(
        self,
        text: str,
        language: str,
    ) -> list[PIIEntity]:
        ...