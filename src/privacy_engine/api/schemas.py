from typing import Literal
from uuid import UUID

from pydantic import BaseModel, field_validator

SupportedLanguage = Literal[
    "de",
    "fr",
    "it",
    "en",
]


class AnonymizeRequest(BaseModel):
    text: str
    language: SupportedLanguage | None = None
    persist: bool = False

    @field_validator("text")
    @classmethod
    def validate_text(
        cls,
        value: str,
    ) -> str:
        if not value.strip():
            raise ValueError(
                "text must not be empty"
            )

        return value


class DetectedEntityResponse(BaseModel):
    entity_type: str
    value: str
    start: int
    end: int


class AnonymizationMappingResponse(BaseModel):
    entity_type: str
    original_value: str
    replacement_value: str


class AnonymizeResponse(BaseModel):
    document_id: UUID
    language: str
    safe_text: str
    entity_count: int
    entities: list[DetectedEntityResponse]
    mappings: list[AnonymizationMappingResponse]