from privacy_engine.domain.entities import PIIEntity
from privacy_engine.domain.providers import PIIProvider


class FakePIIProvider:
    def detect(self, text: str, language: str) -> list[PIIEntity]:
        return [
            PIIEntity(
                entity_type="EMAIL",
                value="adam@example.com",
                start=0,
                end=16,
            )
        ]


def use_provider(
    provider: PIIProvider,
    text: str,
) -> list[PIIEntity]:
    return provider.detect(text, language="en")


def test_provider_contract_accepts_structural_implementation() -> None:
    provider = FakePIIProvider()

    result = use_provider(
        provider,
        "adam@example.com",
    )

    assert len(result) == 1
    assert result[0].entity_type == "EMAIL"