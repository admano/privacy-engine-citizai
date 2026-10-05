import pytest

from privacy_engine.application.entity_resolution import (
    EntityResolver,
)
from privacy_engine.infrastructure.providers.rule_provider import (
    RuleBasedPIIProvider,
)
from tests.evaluation.dataset import (
    load_evaluation_cases,
)
from tests.evaluation.evaluator import (
    evaluate_entities,
)


def create_evaluation_provider() -> RuleBasedPIIProvider:
    return RuleBasedPIIProvider()


@pytest.mark.parametrize(
    "case",
    load_evaluation_cases(),
    ids=lambda case: case.name,
)
def test_detection_quality(case) -> None:
    provider = create_evaluation_provider()
    resolver = EntityResolver()

    detected = provider.detect(
        case.text,
        language="en"
    )

    resolved = resolver.resolve(
        detected
    )

    metrics = evaluate_entities(
        expected=case.expected,
        detected=resolved,
    )

    assert metrics.recall == 1.0
