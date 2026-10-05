import re

import pytest

from privacy_engine.infrastructure.providers.rules.engine import (
    Rule,
    RuleEngine,
)


def test_context_increases_score_within_the_configured_token_window() -> None:
    rule = Rule(
        entity_type="REFERENCE",
        pattern=re.compile(r"\b\d{4}\b"),
        base_score=0.4,
        context_words={"en": ("reference number",)},
        context_boost=0.2,
        context_window_tokens=3,
    )

    entities = RuleEngine((rule,)).detect(
        "The reference number is 1234.",
        language="en",
    )

    assert len(entities) == 1
    assert entities[0].score == pytest.approx(0.6)


def test_context_outside_the_window_does_not_increase_score() -> None:
    rule = Rule(
        entity_type="REFERENCE",
        pattern=re.compile(r"\b\d{4}\b"),
        base_score=0.4,
        context_words={"en": ("reference",)},
        context_boost=0.2,
        context_window_tokens=2,
    )

    entities = RuleEngine((rule,)).detect(
        "reference is separated by several unrelated words 1234",
        language="en",
    )

    assert entities[0].score == 0.4


def test_context_requires_complete_tokens() -> None:
    rule = Rule(
        entity_type="REFERENCE",
        pattern=re.compile(r"\b\d{4}\b"),
        base_score=0.4,
        context_words={"en": ("uid",)},
        context_boost=0.2,
    )

    entities = RuleEngine((rule,)).detect("fluid 1234", language="en")

    assert entities[0].score == 0.4


def test_validator_failure_suppresses_a_match() -> None:
    rule = Rule(
        entity_type="CHECKED",
        pattern=re.compile(r"\b\d{4}\b"),
        base_score=0.8,
        validator=lambda value: value == "1234",
    )

    entities = RuleEngine((rule,)).detect(
        "1234 and 9999",
        language="en",
    )

    assert [entity.value for entity in entities] == ["1234"]
