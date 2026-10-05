from privacy_engine.application.entity_resolution import (
    EntityResolver,
)
from privacy_engine.domain.entities import PIIEntity


def test_normalizes_email_address_to_email() -> None:
    resolver = EntityResolver()

    result = resolver.resolve(
        [
            PIIEntity(
                entity_type="EMAIL_ADDRESS",
                value="adam@example.com",
                start=10,
                end=26,
                score=0.85,
            )
        ]
    )

    assert len(result) == 1
    assert result[0].entity_type == "EMAIL"


def test_removes_duplicate_span_and_keeps_higher_score() -> None:
    resolver = EntityResolver()

    result = resolver.resolve(
        [
            PIIEntity(
                entity_type="EMAIL",
                value="adam@example.com",
                start=10,
                end=26,
                score=0.95,
            ),
            PIIEntity(
                entity_type="EMAIL_ADDRESS",
                value="adam@example.com",
                start=10,
                end=26,
                score=0.80,
            ),
        ]
    )

    assert len(result) == 1
    assert result[0].entity_type == "EMAIL"
    assert result[0].score == 0.95


def test_prefers_larger_entity_when_one_contains_another() -> None:
    resolver = EntityResolver()

    result = resolver.resolve(
        [
            PIIEntity(
                entity_type="PERSON",
                value="Adam",
                start=0,
                end=4,
                score=0.95,
            ),
            PIIEntity(
                entity_type="PERSON",
                value="Adam Taoussi",
                start=0,
                end=11,
                score=0.70,
            ),
        ]
    )

    assert len(result) == 1
    assert result[0].value == "Adam Taoussi"


def test_partial_overlap_prefers_higher_score() -> None:
    resolver = EntityResolver()

    result = resolver.resolve(
        [
            PIIEntity(
                entity_type="PERSON",
                value="Adam Example",
                start=0,
                end=12,
                score=0.60,
            ),
            PIIEntity(
                entity_type="EMAIL",
                value="Example@example.com",
                start=5,
                end=24,
                score=0.95,
            ),
        ]
    )

    assert len(result) == 1
    assert result[0].entity_type == "EMAIL"


def test_bridging_low_score_entity_does_not_drop_unrelated_entities() -> None:
    resolver = EntityResolver()

    result = resolver.resolve(
        [
            PIIEntity(
                entity_type="PERSON",
                value="A",
                start=0,
                end=5,
                score=0.90,
            ),
            PIIEntity(
                entity_type="LOCATION",
                value="B",
                start=10,
                end=15,
                score=0.99,
            ),
            PIIEntity(
                entity_type="ORG",
                value="C",
                start=3,
                end=12,
                score=0.50,
            ),
        ]
    )

    assert [
        (entity.entity_type, entity.start, entity.end)
        for entity in result
    ] == [
        ("PERSON", 0, 5),
        ("LOCATION", 10, 15),
    ]


def test_non_overlapping_entities_are_kept() -> None:
    resolver = EntityResolver()

    result = resolver.resolve(
        [
            PIIEntity(
                entity_type="PERSON",
                value="Adam",
                start=0,
                end=4,
                score=0.90,
            ),
            PIIEntity(
                entity_type="EMAIL",
                value="adam@example.com",
                start=15,
                end=31,
                score=0.95,
            ),
        ]
    )

    assert len(result) == 2