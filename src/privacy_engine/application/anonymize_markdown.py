from uuid import uuid4

from privacy_engine.application.contracts import Anonymizer
from privacy_engine.application.entity_resolution import (
    EntityResolver,
)
from privacy_engine.application.language import (
    LanguageResolver,
)
from privacy_engine.application.markdown_models import (
    MarkdownAnonymizationResult,
    MarkdownDocument,
)
from privacy_engine.application.markdown_processor import (
    MarkdownProcessor,
)
from privacy_engine.application.models import AnonymizationMapping
from privacy_engine.domain.entities import PIIEntity
from privacy_engine.domain.providers import PIIProvider


class AnonymizeMarkdown:
    def __init__(
        self,
        provider: PIIProvider,
        anonymizer: Anonymizer,
        entity_resolver: EntityResolver,
        language_resolver: LanguageResolver,
        markdown_processor: MarkdownProcessor,
    ) -> None:
        self._provider = provider
        self._anonymizer = anonymizer
        self._entity_resolver = entity_resolver
        self._language_resolver = language_resolver
        self._markdown_processor = markdown_processor

    def execute(
        self,
        document: MarkdownDocument,
        language: str | None = None,
    ) -> MarkdownAnonymizationResult:
        resolved_language = (
            self._language_resolver.resolve(
                text=document.content,
                requested_language=language,
            )
        )

        entities: list[PIIEntity] = []
        mappings: list[AnonymizationMapping] = []
        # MarkdownProcessor may call the transform callback once per
        # eligible fragment (e.g. once per line, to keep NER detection
        # accurate). TokenAnonymizer numbers tokens per-type starting
        # from 1 on every call, so token numbers are renumbered here
        # against a document-wide counter to keep them unique and
        # sequential across the whole document instead of restarting
        # per fragment.
        counters: dict[str, int] = {}

        def anonymize_fragment(fragment: str) -> str:
            detected_entities = self._provider.detect(
                text=fragment,
                language=resolved_language.language,
            )

            resolved_entities = self._entity_resolver.resolve(
                detected_entities
            )

            if not resolved_entities:
                return fragment

            anonymizer_result = self._anonymizer.anonymize(
                fragment,
                resolved_entities,
            )

            safe_fragment = anonymizer_result.safe_text

            # EntityResolver.resolve and TokenAnonymizer.anonymize both
            # order their output by ascending start position, so the two
            # sequences line up entity-for-entity here.
            for entity, local_mapping in zip(
                resolved_entities,
                anonymizer_result.mappings,
                strict=True,
            ):
                next_number = (
                    counters.get(local_mapping.entity_type, 0) + 1
                )
                counters[local_mapping.entity_type] = next_number

                global_token = (
                    f"[{local_mapping.entity_type}_{next_number:03d}]"
                )

                safe_fragment = safe_fragment.replace(
                    local_mapping.replacement_value,
                    global_token,
                    1,
                )

                entities.append(entity)
                mappings.append(
                    AnonymizationMapping(
                        entity_type=local_mapping.entity_type,
                        original_value=local_mapping.original_value,
                        replacement_value=global_token,
                    )
                )

            return safe_fragment

        safe_markdown = self._markdown_processor.transform_text(
            document.content,
            anonymize_fragment,
        )

        return MarkdownAnonymizationResult(
            document_id=uuid4(),
            filename=document.filename,
            language=resolved_language.language,
            safe_markdown=safe_markdown,
            is_safe_for_ai=len(entities) == 0,
            entity_count=len(entities),
            entities=tuple(entities),
            mappings=tuple(mappings),
        )
