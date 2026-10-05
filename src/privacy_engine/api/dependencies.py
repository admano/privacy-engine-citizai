from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from privacy_engine.application.anonymization import TokenAnonymizer
from privacy_engine.application.anonymize_and_persist_markdown import (
    AnonymizeAndPersistMarkdown,
)
from privacy_engine.application.anonymize_and_persist_text import (
    AnonymizeAndPersistText,
)
from privacy_engine.application.anonymize_markdown import (
    AnonymizeMarkdown,
)
from privacy_engine.application.anonymize_text import AnonymizeText
from privacy_engine.application.entity_resolution import EntityResolver
from privacy_engine.application.exceptions import DatabaseUnavailableError
from privacy_engine.application.language import LanguageResolver
from privacy_engine.application.markdown_processor import (
    MarkdownProcessor,
)
from privacy_engine.domain.providers import PIIProvider
from privacy_engine.infrastructure.database.repositories import (
    SQLAlchemyMappingRepository,
)
from privacy_engine.infrastructure.language.fasttext_detector import (
    FastTextLanguageDetector,
)
from privacy_engine.infrastructure.markdown.regex_markdown_processor import (
    RegexMarkdownProcessor,
)
from privacy_engine.infrastructure.providers.composite_provider import (
    CompositePIIProvider,
)
from privacy_engine.infrastructure.providers.onnx_ner_provider import (
    OnnxNerPIIProvider,
)
from privacy_engine.infrastructure.providers.rule_provider import (
    RuleBasedPIIProvider,
)


@asynccontextmanager
async def database_session(
    request: Request,
) -> AsyncGenerator[AsyncSession]:
    session_factory = request.app.state.database.session_factory

    try:
        async with session_factory() as session:
            async with session.begin():
                yield session
    except SQLAlchemyError as exc:
        raise DatabaseUnavailableError(
            "Database temporarily unavailable"
        ) from exc


async def get_db_session(
    request: Request,
) -> AsyncIterator[AsyncSession]:
    async with database_session(request) as session:
        yield session


DbSession = Annotated[
    AsyncSession,
    Depends(get_db_session),
]


def _build_pii_provider() -> PIIProvider:
    return CompositePIIProvider(
        providers=(
            RuleBasedPIIProvider(),
            OnnxNerPIIProvider(),
        )
    )


@lru_cache
def get_pii_provider() -> PIIProvider:
    return _build_pii_provider()


def _build_language_resolver() -> LanguageResolver:
    return LanguageResolver(
        detector=FastTextLanguageDetector(),
    )


@lru_cache
def get_language_resolver() -> LanguageResolver:
    return _build_language_resolver()


def get_anonymize_text_use_case() -> AnonymizeText:
    return AnonymizeText(
        provider=get_pii_provider(),
        anonymizer=TokenAnonymizer(),
        entity_resolver=EntityResolver(),
        language_resolver=get_language_resolver(),
    )


def build_anonymize_and_persist_text_use_case(
    anonymize_text: AnonymizeText,
    session: AsyncSession,
) -> AnonymizeAndPersistText:
    return AnonymizeAndPersistText(
        anonymize_text=anonymize_text,
        repository=SQLAlchemyMappingRepository(
            session=session,
        ),
    )


def get_markdown_processor() -> MarkdownProcessor:
    return RegexMarkdownProcessor()


def get_anonymize_markdown_use_case() -> AnonymizeMarkdown:
    return AnonymizeMarkdown(
        provider=get_pii_provider(),
        anonymizer=TokenAnonymizer(),
        entity_resolver=EntityResolver(),
        language_resolver=get_language_resolver(),
        markdown_processor=get_markdown_processor(),
    )


def build_anonymize_and_persist_markdown_use_case(
    anonymize_markdown: AnonymizeMarkdown,
    session: AsyncSession,
) -> AnonymizeAndPersistMarkdown:
    return AnonymizeAndPersistMarkdown(
        anonymize_markdown=anonymize_markdown,
        repository=SQLAlchemyMappingRepository(
            session=session,
        ),
    )
