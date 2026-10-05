import pytest

from privacy_engine.application.entity_resolution import EntityResolver
from privacy_engine.infrastructure.providers.rule_provider import (
    RuleBasedPIIProvider,
)
from tests.evaluation.dataset import load_evaluation_cases
from tests.evaluation.evaluator import evaluate_entities


@pytest.mark.parametrize(
    "case",
    load_evaluation_cases(),
    ids=lambda case: case.name,
)
def test_rule_provider_matches_structured_pii_evaluation_cases(case) -> None:
    detected = RuleBasedPIIProvider().detect(case.text, language="en")
    resolved = EntityResolver().resolve(detected)

    metrics = evaluate_entities(
        expected=case.expected,
        detected=resolved,
    )

    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
