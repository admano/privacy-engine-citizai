import logging

from privacy_engine.infrastructure.providers import onnx_ner_provider


def test_onnx_provider_logs_when_detection_is_invoked(
    caplog,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        onnx_ner_provider,
        "detect_entities",
        lambda text: [],
    )

    with caplog.at_level(
        logging.INFO,
        logger="privacy_engine.infrastructure.onnx_ner",
    ):
        onnx_ner_provider.OnnxNerPIIProvider().detect(
            text="John Smith",
            language="en",
        )

    assert "Local ONNX NER detection invoked" in caplog.messages
