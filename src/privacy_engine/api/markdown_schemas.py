from uuid import UUID

from pydantic import BaseModel, field_validator

from privacy_engine.api.schemas import (
    AnonymizationMappingResponse,
    SupportedLanguage,
)


class AnonymizeMarkdownRequest(BaseModel):
    filename: str
    markdown: str
    language: SupportedLanguage | None = None
    persist: bool = False

    @field_validator("filename")
    @classmethod
    def validate_filename(
        cls,
        value: str,
    ) -> str:
        if not value.strip():
            raise ValueError(
                "filename must not be empty"
            )

        return value

    @field_validator("markdown")
    @classmethod
    def validate_markdown(
        cls,
        value: str,
    ) -> str:
        if not value.strip():
            raise ValueError(
                "markdown must not be empty"
            )

        return value


class DetectedMarkdownEntityResponse(BaseModel):
    entity_type: str
    value: str
    start: int
    end: int


class AnonymizeMarkdownResponse(BaseModel):
    document_id: UUID
    filename: str
    language: str
    safe_markdown: str
    is_safe_for_ai: bool
    entity_count: int
    entities: list[DetectedMarkdownEntityResponse]
    mappings: list[AnonymizationMappingResponse]
