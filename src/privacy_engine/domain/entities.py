from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PIIEntity:
    entity_type: str
    value: str
    start: int
    end: int
    score: float = 1.0