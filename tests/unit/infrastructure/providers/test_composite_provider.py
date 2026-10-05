from privacy_engine.domain.entities import PIIEntity
from privacy_engine.infrastructure.providers.composite_provider import (
    CompositePIIProvider,
)


class PersonProvider:
    def detect(self, text: str, language: str) -> list[PIIEntity]:
        return [
            PIIEntity(
                entity_type="PERSON",
                value="Adam",
                start=0,
                end=4,
            )
        ]


class EmailProvider:
    def detect(self, text: str, language: str) -> list[PIIEntity]:
        return [
            PIIEntity(
                entity_type="EMAIL",
                value="adam@example.com",
                start=15,
                end=31,
            )
        ]


class EmptyProvider:
    def detect(self, text: str, language: str) -> list[PIIEntity]:
        return []


def test_composite_provider_combines_entities() -> None:
    provider = CompositePIIProvider(
        providers=(
            PersonProvider(),
            EmailProvider(),
        )
    )

    entities = provider.detect(
        "Adam email is adam@example.com",
        language="en"
    )

    assert len(entities) == 2
    assert entities[0].entity_type == "PERSON"
    assert entities[1].entity_type == "EMAIL"


def test_composite_provider_orders_entities_by_position() -> None:
    provider = CompositePIIProvider(
        providers=(
            EmailProvider(),
            PersonProvider(),
        )
    )

    entities = provider.detect(
        "Adam email is adam@example.com",
        language="en"
    )

    assert entities[0].entity_type == "PERSON"
    assert entities[1].entity_type == "EMAIL"


def test_composite_provider_supports_empty_provider() -> None:
    provider = CompositePIIProvider(
        providers=(
            EmptyProvider(),
            EmailProvider(),
        )
    )

    entities = provider.detect(
        "Adam email is adam@example.com",
        language="en"
    )

    assert len(entities) == 1
    assert entities[0].entity_type == "EMAIL"


def test_composite_provider_returns_empty_list_when_no_entities_exist() -> None:
    provider = CompositePIIProvider(
        providers=(
            EmptyProvider(),
            EmptyProvider(),
        )
    )

    entities = provider.detect(
        "Hello world",
        language="en"
    )

    assert entities == []