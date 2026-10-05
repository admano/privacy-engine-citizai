from privacy_engine.application.entity_resolution import (
    EntityResolver,
)
from privacy_engine.infrastructure.providers.rule_provider import (
    RuleBasedPIIProvider,
)
from tests.evaluation.dataset import load_evaluation_cases


def test_detection_dataset_has_no_false_negatives() -> None:
    provider = RuleBasedPIIProvider()

    resolver = EntityResolver()

    missed = []

    for case in load_evaluation_cases():
        detected = resolver.resolve(
            provider.detect(case.text, language="en")
        )

        detected_keys = {
            (
                entity.entity_type,
                entity.start,
                entity.end,
            )
            for entity in detected
        }

        for expected in case.expected:
            key = (
                expected.entity_type,
                expected.start,
                expected.end,
            )

            if key not in detected_keys:
                missed.append(
                    f"{case.name}: {expected.entity_type}"
                )

    assert missed == []
