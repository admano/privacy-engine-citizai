from privacy_engine.infrastructure.providers.regex_provider import (
    RegexPIIProvider,
)


def test_detect_single_email() -> None:
    provider = RegexPIIProvider()

    text = "Contact me at adam@example.com"

    result = provider.detect(text, language="en")

    assert len(result) == 1

    entity = result[0]

    assert entity.entity_type == "EMAIL"
    assert entity.value == "adam@example.com"
    assert text[entity.start:entity.end] == "adam@example.com"

def test_detect_returns_empty_list_when_no_email_exists() -> None:
    provider = RegexPIIProvider()

    result = provider.detect("There is no email here.", language="en")

    assert result == []

def test_detect_returns_empty_list_for_empty_text() -> None:
    provider = RegexPIIProvider()

    result = provider.detect("",language="en")

    assert result == []

def test_detect_multiple_emails_in_text_order() -> None:
    provider = RegexPIIProvider()

    text = (
        "Primary: adam@example.com, "
        "secondary: sara@example.org"
    )

    result = provider.detect(text, language="en")

    assert len(result) == 2

    assert result[0].value == "adam@example.com"
    assert result[1].value == "sara@example.org"

    assert text[result[0].start:result[0].end] == "adam@example.com"
    assert text[result[1].start:result[1].end] == "sara@example.org"

def test_detect_email_does_not_include_trailing_punctuation() -> None:
    provider = RegexPIIProvider()

    text = "Send it to adam@example.com."

    result = provider.detect(text, language="en")

    assert len(result) == 1
    assert result[0].value == "adam@example.com"