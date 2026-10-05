# ADR-001: Architecture and core flow

## Status

Accepted

## Decision

The privacy engine uses four layers with dependencies pointing inward:

| Layer | Owns | Must not depend on |
|---|---|---|
| Domain | `PIIEntity`, `PIIProvider` | FastAPI, Pydantic, SQLAlchemy, databases, detector libraries |
| Application | use cases, anonymization, language and entity resolution, repository and Markdown ports | concrete adapters |
| Infrastructure | detection, language, Markdown, and PostgreSQL adapters | API routes |
| API | FastAPI DTOs, routes, error mapping, dependency wiring | business rules |

The public processing contract is:

```text
input + optional language
  -> LanguageResolver
  -> configured PIIProvider (default: local ONNX NER)
  -> EntityResolver
  -> Anonymizer
  -> result with document_id, safe text, entities, and mappings
```

`PIIProvider.detect(text, language)` and `Anonymizer.anonymize(text,
entities)` are structural Python protocols. `PIIEntity` is immutable and has
an entity type, original value, source offsets, and confidence score.

The default anonymizer replaces PII with tokens such as `[EMAIL_001]`, ordered
left-to-right per entity type. It returns both safe text and mappings of
original to replacement values. Each operation receives a UUID `document_id`.

Language is resolved once per operation. A caller-provided supported language
has priority; otherwise a detector selects one of `de`, `fr`, `it`, or `en`.

`EntityResolver` owns shared entity policy before anonymization:

- normalize `EMAIL_ADDRESS` to `EMAIL`, `PHONE_NUMBER` to `PHONE`, and
  `IBAN_CODE` to `CH_IBAN`;
- retain the higher-scoring exact duplicate;
- prevent overlapping replacements: containing spans win, then confidence,
  then span length; and
- return entities in source order.

## Implementation rules

- Domain and application code must not import concrete detection, Markdown,
  web, or database libraries.
- Routes validate and map data only; they do not detect, anonymize, or create
  repositories directly.
- New business logic requires type hints and unit tests.
- CPU-bound detection is called from a worker thread by the API or persistence
  orchestration layer, not by the domain.

## Implemented specification

### Core types and flow

`PIIEntity` is a frozen, slotted dataclass with `entity_type`, `value`,
`start`, `end`, and `score` (default `1.0`). Offsets are zero-based,
end-exclusive character offsets into the exact input handed to a provider.
Providers must not mutate input or return overlapping replacements as a
requirement; overlap handling belongs to `EntityResolver`.

`AnonymizeText.execute(text, language)` performs exactly this sequence:

1. Resolve the language.
2. Detect entities with the configured provider.
3. Resolve aliases, duplicates, and overlaps.
4. Replace the resolved spans and return a new UUID document ID, the resolved
   language, safe text, entities, and mappings.

The supported languages are exactly `de`, `fr`, `it`, and `en`. A supplied
supported language wins with confidence `1.0`; an unsupported language raises
`ValueError`. Without a supplied language, the detector result is used.

### Resolution and replacement rules

Normalize only `EMAIL_ADDRESS -> EMAIL`, `PHONE_NUMBER -> PHONE`, and
`IBAN_CODE -> CH_IBAN`. Deduplicate entities that have the same `(start, end)`
by retaining the first unless a later entity has a strictly higher score.
For intersecting spans, a containing span wins; otherwise higher score wins;
otherwise the longer span wins; an exact tie keeps the first candidate. Return
the final entities ordered by `(start, end)`.

`TokenAnonymizer` processes resolved entities in source order, numbers each
entity type independently from one, and uses `[TYPE_001]` formatting. It makes
replacements right-to-left so original offsets remain valid. Mappings are in
source order and contain `entity_type`, `original_value`, and
`replacement_value`.

### Required module boundaries

Recreate the following dependency direction:

```text
domain: entities.py, providers.py
application: use cases, contracts, resolver, language, repository/Markdown ports
infrastructure: providers, language, Markdown, database, configuration
api: FastAPI schemas, routes, middleware, dependency composition
```

Only API dependency composition may instantiate concrete infrastructure
adapters. Provider and detector implementations are constructor-injected into
application use cases. The public `PIIProvider` contract is
`detect(text: str, language: str) -> list[PIIEntity]`; the anonymizer contract
is `anonymize(text: str, entities: list[PIIEntity]) -> AnonymizerResult`.

The API composition root in `api/dependencies.py` is the only place that
selects a concrete provider. The regenerated default must instantiate exactly
one `OnnxNerPIIProvider`; it must not wrap that provider in a composite or add
a rule, regex, Presidio, or remote provider. Other adapters may remain
import-safe infrastructure code, but they are inactive by default.
