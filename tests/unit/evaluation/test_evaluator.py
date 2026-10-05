from privacy_engine.domain.entities import PIIEntity
from tests.evaluation.evaluator import evaluate_entities
from tests.evaluation.models import ExpectedEntity


def test_evaluator_returns_perfect_score_for_exact_match() -> None:
    expected = (
        ExpectedEntity(
            entity_type="EMAIL",
            value="adam@example.com",
            start=8,
            end=24,
        ),
    )

    detected = [
        PIIEntity(
            entity_type="EMAIL",
            value="adam@example.com",
            start=8,
            end=24,
            score=0.95,
        )
    ]

    metrics = evaluate_entities(
        expected=expected,
        detected=detected,
    )

    assert metrics.true_positives == 1
    assert metrics.false_positives == 0
    assert metrics.false_negatives == 0
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1 == 1.0


def test_evaluator_counts_false_positive() -> None:
    metrics = evaluate_entities(
        expected=(),
        detected=[
            PIIEntity(
                entity_type="PERSON",
                value="Something",
                start=0,
                end=9,
                score=0.6,
            )
        ],
    )

    assert metrics.true_positives == 0
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 0
    assert metrics.precision == 0.0


def test_evaluator_counts_false_negative() -> None:
    expected = (
        ExpectedEntity(
            entity_type="EMAIL",
            value="adam@example.com",
            start=8,
            end=24,
        ),
    )

    metrics = evaluate_entities(
        expected=expected,
        detected=[],
    )

    assert metrics.false_negatives == 1
    assert metrics.recall == 0.0