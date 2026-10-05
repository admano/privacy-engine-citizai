from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExpectedEntity:
    entity_type: str
    value: str
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    name: str
    text: str
    expected: tuple[ExpectedEntity, ...]


@dataclass(frozen=True, slots=True)
class EvaluationMetrics:
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float