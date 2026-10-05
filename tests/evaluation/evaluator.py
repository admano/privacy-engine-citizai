from privacy_engine.domain.entities import PIIEntity
from tests.evaluation.models import (
    EvaluationMetrics,
    ExpectedEntity,
)


def _entity_key(
    entity: PIIEntity | ExpectedEntity,
) -> tuple[str, int, int]:
    return (
        entity.entity_type,
        entity.start,
        entity.end,
    )


def evaluate_entities(
    expected: tuple[ExpectedEntity, ...],
    detected: list[PIIEntity],
) -> EvaluationMetrics:
    expected_keys = {
        _entity_key(entity)
        for entity in expected
    }

    detected_keys = {
        _entity_key(entity)
        for entity in detected
    }

    true_positives = len(
        expected_keys & detected_keys
    )

    false_positives = len(
        detected_keys - expected_keys
    )

    false_negatives = len(
        expected_keys - detected_keys
    )

    precision = (
        true_positives
        / (true_positives + false_positives)
        if true_positives + false_positives
        else 1.0
    )

    recall = (
        true_positives
        / (true_positives + false_negatives)
        if true_positives + false_negatives
        else 1.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if precision + recall
        else 0.0
    )

    return EvaluationMetrics(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        precision=precision,
        recall=recall,
        f1=f1,
    )