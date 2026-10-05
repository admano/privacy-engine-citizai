import asyncio

from privacy_engine.application.anonymize_text import AnonymizeText
from privacy_engine.application.models import AnonymizationResult
from privacy_engine.application.repositories import MappingRepository


class AnonymizeAndPersistText:
    def __init__(
        self,
        anonymize_text: AnonymizeText,
        repository: MappingRepository,
    ) -> None:
        self._anonymize_text = anonymize_text
        self._repository = repository

    async def execute(
        self,
        text: str,
        language: str | None = None,
    ) -> AnonymizationResult:
        # Detection can be CPU-bound (e.g. NLP-based providers), so it is
        # run off the event loop even though AnonymizeText itself stays a
        # plain synchronous, framework-independent use case.
        result = await asyncio.to_thread(
            self._anonymize_text.execute,
            text,
            language,
        )

        if result.mappings:
            await self._repository.save(
                document_id=result.document_id,
                mappings=result.mappings,
            )

        return result