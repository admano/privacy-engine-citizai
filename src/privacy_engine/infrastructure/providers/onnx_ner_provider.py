"""Local ONNX token-classification adapter for named-entity detection."""

import logging
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any

from privacy_engine.domain.entities import PIIEntity

_MODEL_DIRECTORY = Path(__file__).resolve().parents[4] / "pii-ner"
_ENTITY_TYPES = {
    "PER": "PERSON",
    "LOC": "LOCATION",
    "ORG": "ORGANIZATION",
}
logger = logging.getLogger("privacy_engine.infrastructure.onnx_ner")


def default_model_path() -> Path:
    """Return the checked-in model directory without relying on ``cwd``."""
    return _MODEL_DIRECTORY


@lru_cache
def get_ner_pipeline(model_path: Path) -> Callable[[str], list[dict[str, Any]]]:
    """Create the local-only NER pipeline once for each model directory."""
    from optimum.onnxruntime import ORTModelForTokenClassification
    from transformers import AutoTokenizer, pipeline

    resolved_path = model_path.resolve()
    if not resolved_path.is_dir():
        raise FileNotFoundError(
            f"Local ONNX NER model directory does not exist: {resolved_path}"
        )

    tokenizer = AutoTokenizer.from_pretrained(
        resolved_path,
        local_files_only=True,
        use_fast=True,
        # This is a DistilBERT tokenizer, not a Mistral tokenizer. Recent
        # Transformers releases can otherwise issue a false-positive warning
        # and attempt an incompatible Mistral pre-tokenizer mutation.
        fix_mistral_regex=False,
    )
    model = ORTModelForTokenClassification.from_pretrained(
        resolved_path,
        local_files_only=True,
    )
    return pipeline(
        "token-classification",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="simple",
        device=-1,
    )


def detect_entities(text: str) -> list[dict[str, Any]]:
    """Detect entities with the bundled local model.

    Results use the project's entity vocabulary and contain only plain Python
    values so callers can safely serialize them.
    """
    if not text:
        return []

    results = get_ner_pipeline(default_model_path())(text)
    return [
        {
            "type": _ENTITY_TYPES.get(result["entity_group"], result["entity_group"]),
            "text": result["word"],
            "score": float(result["score"]),
            "start": result["start"],
            "end": result["end"],
        }
        for result in results
    ]


class OnnxNerPIIProvider:
    """Adapt the bundled ONNX NER model to the domain PII provider port."""

    def detect(
        self,
        text: str,
        language: str,
    ) -> list[PIIEntity]:
        del language  # The multilingual model selects labels independently.
        if text:
            logger.info("Local ONNX NER detection invoked")
        return [
            PIIEntity(
                entity_type=result["type"],
                value=result["text"],
                start=result["start"],
                end=result["end"],
                score=result["score"],
            )
            for result in detect_entities(text)
        ]
