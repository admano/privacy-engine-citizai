from pathlib import Path

import pytest

pytest.importorskip("optimum.onnxruntime")

from privacy_engine.infrastructure.providers.onnx_ner_provider import (
    default_model_path,
    detect_entities,
    get_ner_pipeline,
)


def test_detects_a_person() -> None:
    entities = detect_entities("My name is John Smith.")

    assert any(
        entity["type"] == "PERSON" and entity["text"] == "John Smith"
        for entity in entities
    )


def test_detects_a_location() -> None:
    entities = detect_entities("I live in Zurich.")

    assert any(
        entity["type"] == "LOCATION" and entity["text"] == "Zurich"
        for entity in entities
    )


def test_detects_an_organization() -> None:
    entities = detect_entities("I work for Google.")

    assert any(
        entity["type"] == "ORGANIZATION" and entity["text"] == "Google"
        for entity in entities
    )


def test_empty_text_does_not_load_or_run_the_model() -> None:
    assert detect_entities("") == []


def test_loads_the_bundled_model_from_a_local_path() -> None:
    model_path = default_model_path()

    assert model_path == Path(__file__).resolve().parents[4] / "pii-ner"
    assert model_path.is_dir()
    assert callable(get_ner_pipeline(model_path))
