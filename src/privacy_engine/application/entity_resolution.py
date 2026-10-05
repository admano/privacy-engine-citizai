from privacy_engine.domain.entities import PIIEntity

_ENTITY_TYPE_ALIASES = {
    "EMAIL_ADDRESS": "EMAIL",
    "PHONE_NUMBER": "PHONE",
    "IBAN_CODE": "CH_IBAN",
}


class EntityResolver:
    def resolve(
        self,
        entities: list[PIIEntity],
    ) -> list[PIIEntity]:
        normalized = [
            self._normalize(entity)
            for entity in entities
        ]

        deduplicated = self._deduplicate(normalized)

        resolved = self._resolve_overlaps(deduplicated)

        return sorted(
            resolved,
            key=lambda entity: (
                entity.start,
                entity.end,
            ),
        )

    def _normalize(
        self,
        entity: PIIEntity,
    ) -> PIIEntity:
        normalized_type = _ENTITY_TYPE_ALIASES.get(
            entity.entity_type,
            entity.entity_type,
        )

        if normalized_type == entity.entity_type:
            return entity

        return PIIEntity(
            entity_type=normalized_type,
            value=entity.value,
            start=entity.start,
            end=entity.end,
            score=entity.score,
        )

    def _deduplicate(
        self,
        entities: list[PIIEntity],
    ) -> list[PIIEntity]:
        best_by_span: dict[
            tuple[int, int],
            PIIEntity,
        ] = {}

        for entity in entities:
            key = (
                entity.start,
                entity.end,
            )

            existing = best_by_span.get(key)

            if existing is None:
                best_by_span[key] = entity
                continue

            if entity.score > existing.score:
                best_by_span[key] = entity

        return list(best_by_span.values())

    def _resolve_overlaps(
        self,
        entities: list[PIIEntity],
    ) -> list[PIIEntity]:
        candidates = sorted(
            entities,
            key=lambda entity: (
                entity.start,
                -(entity.end - entity.start),
                -entity.score,
            ),
        )

        resolved: list[PIIEntity] = []

        for candidate in candidates:
            overlapping = [
                entity
                for entity in resolved
                if self._overlaps(
                    candidate,
                    entity,
                )
            ]

            if not overlapping:
                resolved.append(candidate)
                continue

            # `resolved` never contains two entities that overlap each
            # other, so every entry in `overlapping` only conflicts with
            # `candidate`, not with one another. The candidate can only
            # replace them if it individually beats every one of them;
            # otherwise it is dropped and the existing entries (which
            # remain mutually non-overlapping) are left untouched.
            candidate_wins = all(
                self._choose_winner(candidate, existing) is candidate
                for existing in overlapping
            )

            if not candidate_wins:
                continue

            resolved = [
                entity
                for entity in resolved
                if entity not in overlapping
            ]
            resolved.append(candidate)

        return resolved

    @staticmethod
    def _overlaps(
        first: PIIEntity,
        second: PIIEntity,
    ) -> bool:
        return (
            first.start < second.end
            and second.start < first.end
        )

    @staticmethod
    def _contains(
        outer: PIIEntity,
        inner: PIIEntity,
    ) -> bool:
        return (
            outer.start <= inner.start
            and outer.end >= inner.end
        )

    def _choose_winner(
        self,
        first: PIIEntity,
        second: PIIEntity,
    ) -> PIIEntity:
        if self._contains(first, second):
            return first

        if self._contains(second, first):
            return second

        if first.score > second.score:
            return first

        if second.score > first.score:
            return second

        first_length = first.end - first.start
        second_length = second.end - second.start

        if first_length >= second_length:
            return first

        return second