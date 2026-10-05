from privacy_engine.infrastructure.providers.rule_provider import (
    RuleBasedPIIProvider,
)


def test_detects_generic_and_swiss_structured_pii() -> None:
    text = (
        "Email adam@example.com, IBAN CH93 0076 2011 6238 5295 7, "
        "AHV 756.1234.5678.97, UID CHE-123.456.788, "
        "phone +41 79 123 45 67, card 4111 1111 1111 1111, "
        "IP 192.168.1.10, and https://example.com/path."
    )

    entities = RuleBasedPIIProvider().detect(text, language="en")

    assert {entity.entity_type for entity in entities} == {
        "EMAIL",
        "CH_IBAN",
        "CH_AHV",
        "CH_UID",
        "CH_PHONE",
        "CREDIT_CARD",
        "IP_ADDRESS",
        "URL",
    }
    assert all(text[entity.start:entity.end] == entity.value for entity in entities)


def test_rejects_invalid_checksum_values() -> None:
    text = (
        "756.1234.5678.98 CH93 0076 2011 6238 5295 8 "
        "CHE-123.456.789 4111 1111 1111 1112"
    )

    entities = RuleBasedPIIProvider().detect(text, language="en")

    assert entities == []


def test_phone_context_increases_score() -> None:
    provider = RuleBasedPIIProvider()

    without_context = provider.detect("Call 079 123 45 67", language="en")
    with_context = provider.detect(
        "Phone number: 079 123 45 67",
        language="en",
    )

    without_phone = next(
        entity for entity in without_context if entity.entity_type == "CH_PHONE"
    )
    with_phone = next(
        entity for entity in with_context if entity.entity_type == "CH_PHONE"
    )

    assert with_phone.score > without_phone.score

