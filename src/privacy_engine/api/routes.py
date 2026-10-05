import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from privacy_engine.api.dependencies import (
    build_anonymize_and_persist_markdown_use_case,
    build_anonymize_and_persist_text_use_case,
    database_session,
    get_anonymize_markdown_use_case,
    get_anonymize_text_use_case,
)
from privacy_engine.api.markdown_schemas import (
    AnonymizeMarkdownRequest,
    AnonymizeMarkdownResponse,
    DetectedMarkdownEntityResponse,
)
from privacy_engine.api.schemas import (
    AnonymizationMappingResponse,
    AnonymizeRequest,
    AnonymizeResponse,
    DetectedEntityResponse,
)
from privacy_engine.application.anonymize_markdown import (
    AnonymizeMarkdown,
)
from privacy_engine.application.anonymize_text import AnonymizeText
from privacy_engine.application.markdown_models import MarkdownDocument
from privacy_engine.application.models import AnonymizationMapping

router = APIRouter(
    prefix="/privacy",
)


def _mapping_responses(
    mappings: tuple[AnonymizationMapping, ...],
) -> list[AnonymizationMappingResponse]:
    return [
        AnonymizationMappingResponse(
            entity_type=mapping.entity_type,
            original_value=mapping.original_value,
            replacement_value=mapping.replacement_value,
        )
        for mapping in mappings
    ]


@router.post(
    "/anonymize",
    response_model=AnonymizeResponse,
)
async def anonymize_text(
    request_body: AnonymizeRequest,
    request: Request,
    anonymize_use_case: Annotated[
        AnonymizeText,
        Depends(get_anonymize_text_use_case),
    ],
) -> AnonymizeResponse:

    if request_body.persist:
        # Only touch the database when persistence is actually requested
        # (ADR-007) - hence the manual, conditional session acquisition
        # instead of an unconditional `Depends(...)` parameter.
        async with database_session(request) as session:
            persist_use_case = build_anonymize_and_persist_text_use_case(
                anonymize_text=anonymize_use_case,
                session=session,
            )

            result = await persist_use_case.execute(
                text=request_body.text,
                language=request_body.language,
            )

    else:
        # AnonymizeText.execute is CPU-bound (NLP detection), so it is
        # offloaded to a worker thread instead of blocking the event loop.
        result = await asyncio.to_thread(
            anonymize_use_case.execute,
            request_body.text,
            request_body.language,
        )

    return AnonymizeResponse(
        document_id=result.document_id,
        language=result.language,
        safe_text=result.safe_text,
        entity_count=result.entity_count,
        entities=[
            DetectedEntityResponse(
                entity_type=entity.entity_type,
                value=entity.value,
                start=entity.start,
                end=entity.end,
            )
            for entity in result.entities
        ],
        mappings=_mapping_responses(result.mappings),
    )


@router.post(
    "/anonymize/markdown",
    response_model=AnonymizeMarkdownResponse,
)
async def anonymize_markdown(
    request_body: AnonymizeMarkdownRequest,
    request: Request,
    anonymize_use_case: Annotated[
        AnonymizeMarkdown,
        Depends(get_anonymize_markdown_use_case),
    ],
) -> AnonymizeMarkdownResponse:

    document = MarkdownDocument(
        filename=request_body.filename,
        content=request_body.markdown,
    )

    if request_body.persist:
        # Only touch the database when persistence is actually requested
        # (ADR-007, ADR-012) - hence the manual, conditional session
        # acquisition instead of an unconditional `Depends(...)` parameter.
        async with database_session(request) as session:
            persist_use_case = (
                build_anonymize_and_persist_markdown_use_case(
                    anonymize_markdown=anonymize_use_case,
                    session=session,
                )
            )

            result = await persist_use_case.execute(
                document=document,
                language=request_body.language,
            )

    else:
        # AnonymizeMarkdown.execute is CPU-bound (NLP detection), so it
        # is offloaded to a worker thread instead of blocking the event
        # loop.
        result = await asyncio.to_thread(
            anonymize_use_case.execute,
            document,
            request_body.language,
        )

    return AnonymizeMarkdownResponse(
        document_id=result.document_id,
        filename=result.filename,
        language=result.language,
        safe_markdown=result.safe_markdown,
        is_safe_for_ai=result.is_safe_for_ai,
        entity_count=result.entity_count,
        entities=[
            DetectedMarkdownEntityResponse(
                entity_type=entity.entity_type,
                value=entity.value,
                start=entity.start,
                end=entity.end,
            )
            for entity in result.entities
        ],
        mappings=_mapping_responses(result.mappings),
    )
