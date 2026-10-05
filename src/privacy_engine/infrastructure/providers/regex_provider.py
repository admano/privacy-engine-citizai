import re

from privacy_engine.domain.entities import PIIEntity


class RegexPIIProvider:
    _EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

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
                score=0.95,
            )
            for match in self._EMAIL_PATTERN.finditer(text)
        ]