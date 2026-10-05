from privacy_engine.application.anonymization import TokenAnonymizer
from privacy_engine.domain.entities import PIIEntity


def test_anonymize_single_email() -> None:
    anonymizer = TokenAnonymizer()

    text = "Contact me at adam@example.com"

    entities = [
        PIIEntity(
            entity_type="EMAIL",
            value="adam@example.com",
            start=14,
            end=30,
        )
    ]

    result = anonymizer.anonymize(text, entities)

    assert result.safe_text == "Contact me at [EMAIL_001]"

def test_anonymize_returns_original_text_when_no_entities_exist() -> None:
    anonymizer = TokenAnonymizer()

    text = "Nothing sensitive here."

    result = anonymizer.anonymize(text, [])

    assert result.safe_text == text
    assert result.mappings == ()

def test_anonymize_numbers_same_entity_type_in_text_order() -> None:
    anonymizer = TokenAnonymizer()

    text = "adam@example.com and sara@example.com"

    entities = [
        PIIEntity(
            entity_type="EMAIL",
            value="adam@example.com",
            start=0,
            end=16,
        ),
        PIIEntity(
            entity_type="EMAIL",
            value="sara@example.com",
            start=21,
            end=37,
        ),
    ]

    result = anonymizer.anonymize(text, entities)

    assert result.safe_text == "[EMAIL_001] and [EMAIL_002]"


def test_anonymize_numbers_entity_types_independently() -> None:
    anonymizer = TokenAnonymizer()

    text = "Adam: adam@example.com"

    entities = [
        PIIEntity(
            entity_type="PERSON",
            value="Adam",
            start=0,
            end=4,
        ),
        PIIEntity(
            entity_type="EMAIL",
            value="adam@example.com",
            start=6,
            end=22,
        ),
    ]

    result = anonymizer.anonymize(text, entities)

    assert result.safe_text == "[PERSON_001]: [EMAIL_001]"


def test_anonymize_handles_entities_not_sorted_by_position() -> None:
    anonymizer = TokenAnonymizer()

    text = "Adam: adam@example.com"

    entities = [
        PIIEntity(
            entity_type="EMAIL",
            value="adam@example.com",
            start=6,
            end=22,
        ),
        PIIEntity(
            entity_type="PERSON",
            value="Adam",
            start=0,
            end=4,
        ),
    ]

    result = anonymizer.anonymize(text, entities)

    assert result.safe_text == "[PERSON_001]: [EMAIL_001]"




def test_anonymize_single_email_returns_mapping() -> None:
    anonymizer = TokenAnonymizer()

    text = "Contact me at adam@example.com"
    email = "adam@example.com"

    start = text.index(email)

    entities = [
        PIIEntity(
            entity_type="EMAIL",
            value=email,
            start=start,
            end=start + len(email),
        )
    ]

    result = anonymizer.anonymize(text, entities)

    assert result.safe_text == "Contact me at [EMAIL_001]"

    assert len(result.mappings) == 1

    mapping = result.mappings[0]

    assert mapping.entity_type == "EMAIL"
    assert mapping.original_value == "adam@example.com"
    assert mapping.replacement_value == "[EMAIL_001]"

def test_anonymize_returns_mapping_for_each_detected_entity() -> None:
    anonymizer = TokenAnonymizer()

    text = "adam@example.com and sara@example.com"

    first = "adam@example.com"
    second = "sara@example.com"

    first_start = text.index(first)
    second_start = text.index(second)

    entities = [
        PIIEntity(
            entity_type="EMAIL",
            value=first,
            start=first_start,
            end=first_start + len(first),
        ),
        PIIEntity(
            entity_type="EMAIL",
            value=second,
            start=second_start,
            end=second_start + len(second),
        ),
    ]

    result = anonymizer.anonymize(text, entities)

    assert result.safe_text == "[EMAIL_001] and [EMAIL_002]"

    assert [mapping.replacement_value for mapping in result.mappings] == [
        "[EMAIL_001]",
        "[EMAIL_002]",
    ]