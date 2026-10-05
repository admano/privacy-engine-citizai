from uuid import uuid4

from privacy_engine.application.contracts import Anonymizer
from privacy_engine.application.entity_resolution import (
    EntityResolver,
)
from privacy_engine.application.language import (
    LanguageResolver,
)
from privacy_engine.application.models import (
    AnonymizationResult,
)
from privacy_engine.domain.providers import PIIProvider


class AnonymizeText:
    def __init__(
        self,
        provider: PIIProvider,
        anonymizer: Anonymizer,
        entity_resolver: EntityResolver,
        language_resolver: LanguageResolver,
    ) -> None:
        self._provider = provider
        self._anonymizer = anonymizer
        self._entity_resolver = entity_resolver
        self._language_resolver = language_resolver

    def execute(
        self,
        text: str,
        language: str | None = None,
    ) -> AnonymizationResult:
        resolved_language = (
            self._language_resolver.resolve(
                text=text,
                requested_language=language,
            )
        )

        detected_entities = self._provider.detect(
            text=text,
            language=resolved_language.language,
        )

        entities = self._entity_resolver.resolve(
            detected_entities
        )

        anonymizer_result = self._anonymizer.anonymize(
            text,
            entities,
        )

        return AnonymizationResult(
            document_id=uuid4(),
            language=resolved_language.language,
            safe_text=anonymizer_result.safe_text,
            entity_count=len(entities),
            entities=tuple(entities),
            mappings=anonymizer_result.mappings,
        )