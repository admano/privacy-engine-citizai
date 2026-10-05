import json
from pathlib import Path

from tests.evaluation.models import (
    EvaluationCase,
    ExpectedEntity,
)

DATASET_PATH = (
    Path(__file__).parent
    / "pii_detection_cases.json"
)


def load_evaluation_cases() -> tuple[EvaluationCase, ...]:
    data = json.loads(
        DATASET_PATH.read_text(
            encoding="utf-8",
        )
    )

    return tuple(
        EvaluationCase(
            name=item["name"],
            text=item["text"],
            expected=tuple(
                ExpectedEntity(
                    entity_type=entity["entity_type"],
                    value=entity["value"],
                    start=entity["start"],
                    end=entity["end"],
                )
                for entity in item["expected"]
            ),
        )
        for item in data
    )