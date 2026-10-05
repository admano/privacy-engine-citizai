from dataclasses import dataclass
from uuid import UUID

from privacy_engine.application.models import AnonymizationMapping
from privacy_engine.domain.entities import PIIEntity


@dataclass(frozen=True, slots=True)
class MarkdownDocument:
    filename: str
    content: str


@dataclass(frozen=True, slots=True)
class MarkdownAnonymizationResult:
    document_id: UUID
    filename: str
    language: str
    safe_markdown: str
    is_safe_for_ai: bool
    entity_count: int
    entities: tuple[PIIEntity, ...]
    mappings: tuple[AnonymizationMapping, ...]
