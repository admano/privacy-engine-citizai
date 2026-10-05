from privacy_engine.domain.entities import PIIEntity
from privacy_engine.domain.providers import PIIProvider


class CompositePIIProvider:
    def __init__(
        self,
        providers: tuple[PIIProvider, ...],
    ) -> None:
        self._providers = providers

    def detect(
        self,
        text: str,
        language: str,
    ) -> list[PIIEntity]:
        entities: list[PIIEntity] = []

        for provider in self._providers:
            entities.extend(
                provider.detect(
                    text=text,
                    language=language,
                )
            )

        return sorted(
            entities,
            key=lambda entity: (
                entity.start,
                entity.end,
            ),
        )