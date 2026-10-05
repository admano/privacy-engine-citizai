from dataclasses import dataclass
from uuid import UUID

from privacy_engine.domain.entities import PIIEntity


@dataclass(frozen=True, slots=True)
class AnonymizationMapping:
    entity_type: str
    original_value: str
    replacement_value: str


@dataclass(frozen=True, slots=True)
class AnonymizerResult:
    safe_text: str
    mappings: tuple[AnonymizationMapping, ...]


@dataclass(frozen=True, slots=True)
class AnonymizationResult:
    document_id: UUID
    language: str
    safe_text: str
    entity_count: int
    entities: tuple[PIIEntity, ...]
    mappings: tuple[AnonymizationMapping, ...]