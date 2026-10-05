import asyncio

from privacy_engine.application.anonymize_markdown import (
    AnonymizeMarkdown,
)
from privacy_engine.application.markdown_models import (
    MarkdownAnonymizationResult,
    MarkdownDocument,
)
from privacy_engine.application.repositories import MappingRepository


class AnonymizeAndPersistMarkdown:
    def __init__(
        self,
        anonymize_markdown: AnonymizeMarkdown,
        repository: MappingRepository,
    ) -> None:
        self._anonymize_markdown = anonymize_markdown
        self._repository = repository

    async def execute(
        self,
        document: MarkdownDocument,
        language: str | None = None,
    ) -> MarkdownAnonymizationResult:
        # Detection can be CPU-bound (e.g. NLP-based providers), so it is
        # run off the event loop even though AnonymizeMarkdown itself
        # stays a plain synchronous, framework-independent use case.
        result = await asyncio.to_thread(
            self._anonymize_markdown.execute,
            document,
            language,
        )

        if result.mappings:
            await self._repository.save(
                document_id=result.document_id,
                mappings=result.mappings,
            )

        return result
