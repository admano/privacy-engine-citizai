from collections import defaultdict

from privacy_engine.application.models import (
    AnonymizationMapping,
    AnonymizerResult,
)
from privacy_engine.domain.entities import PIIEntity


class TokenAnonymizer:
    def anonymize(
        self,
        text: str,
        entities: list[PIIEntity],
    ) -> AnonymizerResult:
        if not entities:
            return AnonymizerResult(
                safe_text=text,
                mappings=(),
            )

        ordered_entities = sorted(
            entities,
            key=lambda entity: entity.start,
        )

        counters: dict[str, int] = defaultdict(int)

        replacements: list[
            tuple[PIIEntity, AnonymizationMapping]
        ] = []

        for entity in ordered_entities:
            counters[entity.entity_type] += 1

            number = counters[entity.entity_type]
            token = f"[{entity.entity_type}_{number:03d}]"

            mapping = AnonymizationMapping(
                entity_type=entity.entity_type,
                original_value=entity.value,
                replacement_value=token,
            )

            replacements.append(
                (entity, mapping)
            )

        safe_text = text

        for entity, mapping in reversed(replacements):
            safe_text = (
                safe_text[:entity.start]
                + mapping.replacement_value
                + safe_text[entity.end:]
            )

        return AnonymizerResult(
            safe_text=safe_text,
            mappings=tuple(
                mapping
                for _, mapping in replacements
            ),
        )