from privacy_engine.api.dependencies import _build_pii_provider
from privacy_engine.infrastructure.providers.composite_provider import (
    CompositePIIProvider,
)


def test_default_profile_combines_rule_and_onnx_ner_providers() -> None:
    provider = _build_pii_provider()

    assert isinstance(provider, CompositePIIProvider)
