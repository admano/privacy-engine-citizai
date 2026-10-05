import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from privacy_engine.domain.entities import PIIEntity

Validator = Callable[[str], bool]


@dataclass(frozen=True, slots=True)
class Rule:
    entity_type: str
    pattern: re.Pattern[str]
    base_score: float
    validator: Validator | None = None
    context_words: Mapping[str, tuple[str, ...]] = field(
        default_factory=dict,
    )
    context_boost: float = 0.2
    context_window_tokens: int = 5


class RuleEngine:
    def __init__(self, rules: tuple[Rule, ...]) -> None:
        self._rules = rules

    def detect(
        self,
        text: str,
        language: str,
    ) -> list[PIIEntity]:
        entities: list[PIIEntity] = []

        for rule in self._rules:
            entities.extend(self._detect_rule(rule, text, language))

        return sorted(
            entities,
            key=lambda entity: (entity.start, entity.end),
        )

    def _detect_rule(
        self,
        rule: Rule,
        text: str,
        language: str,
    ) -> list[PIIEntity]:
        entities: list[PIIEntity] = []

        for match in rule.pattern.finditer(text):
            value = match.group(0)

            if rule.validator is not None and not rule.validator(value):
                continue

            score = rule.base_score

            if self._has_context(rule, text[:match.start()], language):
                score = min(1.0, score + rule.context_boost)

            entities.append(
                PIIEntity(
                    entity_type=rule.entity_type,
                    value=value,
                    start=match.start(),
                    end=match.end(),
                    score=score,
                )
            )

        return entities

    @staticmethod
    def _has_context(
        rule: Rule,
        prefix: str,
        language: str,
    ) -> bool:
        contexts = rule.context_words.get(language, ())

        if not contexts:
            return False

        window = re.findall(
            r"\w+",
            prefix.casefold(),
        )[-rule.context_window_tokens :]

        return any(
            RuleEngine._contains_context(window, context)
            for context in contexts
        )

    @staticmethod
    def _contains_context(
        window: list[str],
        context: str,
    ) -> bool:
        context_tokens = re.findall(r"\w+", context.casefold())

        if not context_tokens:
            return False

        width = len(context_tokens)

        return any(
            window[index : index + width] == context_tokens
            for index in range(len(window) - width + 1)
        )
