import pytest

from privacy_engine.domain.entities import PIIEntity


def test_pii_entity_contains_detection_information() -> None:
    entity = PIIEntity(
        entity_type="EMAIL",
        value="adam@example.com",
        start=14,
        end=30,
    )

    assert entity.entity_type == "EMAIL"
    assert entity.value == "adam@example.com"
    assert entity.start == 14
    assert entity.end == 30


def test_pii_entity_is_immutable() -> None:
    entity = PIIEntity(
        entity_type="EMAIL",
        value="adam@example.com",
        start=14,
        end=30,
    )

    with pytest.raises(Exception):
        entity.value = "changed@example.com"