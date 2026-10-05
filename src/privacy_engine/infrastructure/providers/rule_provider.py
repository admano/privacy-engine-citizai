from privacy_engine.domain.entities import PIIEntity
from privacy_engine.infrastructure.providers.rules.engine import RuleEngine
from privacy_engine.infrastructure.providers.rules.generic import default_rules
from privacy_engine.infrastructure.providers.rules.swiss import swiss_rules


class RuleBasedPIIProvider:
    def __init__(self) -> None:
        self._engine = RuleEngine(default_rules() + swiss_rules())

    def detect(
        self,
        text: str,
        language: str,
    ) -> list[PIIEntity]:
        return self._engine.detect(text=text, language=language)
