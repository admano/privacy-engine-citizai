# ADR-003: Delivery, persistence, and Markdown

## Status

Accepted for development; sensitive mapping storage needs a production
security decision.

## API and safety

FastAPI is the outer adapter and exposes:

| Endpoint | Behaviour |
|---|---|
| `POST /api/v1/privacy/anonymize` | anonymize text; persist mappings only when requested |
| `POST /api/v1/privacy/anonymize/markdown` | anonymize Markdown with the same privacy pipeline |
| `GET /api/v1/health` | process liveness |
| `GET /api/v1/health/ready` | PostgreSQL readiness |

Pydantic validates request and response DTOs. Missing/blank input and an
unsupported explicit language return 422; known application input errors are
400; database failures are 503; unexpected failures are 500 without internal
details. Request logs contain request ID, method, path, and status only—never
request bodies, original PII, mappings, or database error details.

Every request reuses `X-Request-ID` or receives a new UUID, which is returned
in the response.

## Persistence

Pure `AnonymizeText` and `AnonymizeMarkdown` never persist mappings.
The API selects `AnonymizeAndPersistText` or `AnonymizeAndPersistMarkdown`
only when `persist=true`; it otherwise uses the pure use case. The persistence
use cases save only when mappings exist, and `persist` defaults to `false`.

The application depends on `MappingRepository`; infrastructure provides the
SQLAlchemy/PostgreSQL adapter. One async engine and session factory live for
the process; a short-lived `AsyncSession` and explicit transaction belong to
each request. Repositories receive a session, add and flush rows, and never
commit. Alembic owns schema evolution; application startup must not create
tables from ORM metadata.

All mappings from one operation share its `document_id`. The development
schema stores entity type, original value, replacement value, and document ID.
Original values are sensitive PII and are currently plaintext in development.
Before production, define encryption, access controls, retention, deletion,
key management, and whether reversibility is required.

## Markdown

Markdown uses an application `MarkdownProcessor` port and the same language,
detection, resolution, tokenization, and optional persistence flow as text.
It anonymizes headings, paragraphs, lists, blockquotes, table cells, and link
labels. It preserves Markdown syntax and does not anonymize fenced code,
inline code, link destinations, or image destinations.

One Markdown operation returns one document ID, document-wide sequential
tokens, aggregated entities and mappings, safe Markdown, resolved language,
and `is_safe_for_ai`. The filename is metadata, not an identifier. No mappings
means no persistence rows.

## Implemented specification

### HTTP contract

All endpoints are prefixed with `/api/v1`. Text anonymization accepts
`{"text": string, "language"?: "de"|"fr"|"it"|"en", "persist"?: boolean}`.
Markdown anonymization accepts
`{"filename": string, "markdown": string, "language"?: language,
"persist"?: boolean}`. `text`, `markdown`, and `filename` must contain at
least one non-whitespace character; FastAPI returns 422 for schema or explicit
language validation failures.

Text responses contain `document_id`, `language`, `safe_text`, `entity_count`,
`entities`, and `mappings`; Markdown responses substitute `filename`,
`safe_markdown`, and `is_safe_for_ai` for `safe_text`. An entity has
`entity_type`, `value`, `start`, and `end`. A mapping has `entity_type`,
`original_value`, and `replacement_value`.

`InvalidInputError` maps to `400 {"detail": message}` and database failures
map to `503 {"detail": "Database temporarily unavailable"}`. Other failures
use FastAPI's normal 500 response. `X-Request-ID` is accepted only when it
matches `[A-Za-z0-9_.-]{1,128}`; otherwise a UUID is generated. It is returned
on every completed response and appears in JSON logs with only method, path,
and status. Database failures log only the fixed message `database operation
failed`; exception text and tracebacks must not be logged because they can
contain connection details or PII.

### Persistence and migrations

`persist` defaults to `false`. For `false`, routes run the pure use case in a
worker thread and do not obtain a database session. For `true`, they acquire a
request-scoped async session and transaction, run the persistence orchestration
in a worker thread, then save mappings only when at least one mapping exists.
Repositories add and flush; the route-owned transaction commits or rolls back.

The migration sequence is `3da42872ae61`, which creates
`anonymization_mapping`, then `314b145fd58d`, the current head, which adds
`document_id UUID NOT NULL` and its non-unique index. The final table has
`id BIGINT` primary key, `document_id UUID NOT NULL`,
`entity_type VARCHAR(100) NOT NULL`, `original_value TEXT NOT NULL`, and
`replacement_value VARCHAR(255) NOT NULL`. The async engine uses
`pool_pre_ping=True`; sessions have
`expire_on_commit=False`. Startup creates the engine/session factory and never
creates schema from ORM metadata; use `alembic upgrade head`.

### Markdown transformation contract

`RegexMarkdownProcessor` copies protected spans character-for-character and passes every
other source line, excluding its line terminator, to the normal privacy flow.
It protects fenced backtick/tilde blocks, inline code spans, autolinks,
reference-link definition lines, reference identifiers in `[label][reference]`,
and inline/image link destinations. Headings, prose, lists, blockquotes, table
cells, and link labels remain eligible.

Each eligible line is detected and anonymized independently. Markdown gathers
the resulting entities and mappings under one document ID and renumbers tokens
per entity type across the entire document, so tokens do not restart on later
lines. `is_safe_for_ai` is `true` exactly when no entities were detected.

### Runtime dependencies

Production dependencies are FastAPI, SQLAlchemy, asyncpg, greenlet,
Pydantic Settings, fast-langdetect, python-stdnum, Alembic, onnxruntime,
`optimum[onnxruntime]`, and transformers. Python 3.12 or newer is required.
The development toolchain is pytest, pytest-asyncio, httpx, uvicorn, Ruff, and
mypy. ONNX dependencies are mandatory because ADR-002 makes the bundled local
ONNX model the sole active provider.

`pyproject.toml` is the dependency source of truth. `requirements.txt` is the
repeatable bootstrap entry point and contains `-e .[dev]`; running
`python -m pip install -r requirements.txt` must install every dependency
needed to serve the default API. A future lockfile may be added, but it must
represent these same mandatory dependencies and not change the launch contract.

For local PostgreSQL, `compose.yaml` defines service `postgres` using
`postgres:17`, container `ai-privacy-engine-postgres`, port `5432`, database
`privacy_engine_test`, and credentials `privacy_user` / `privacy_password`.
Its health check is `pg_isready -U privacy_user -d privacy_engine_test` every
five seconds, with a five-second timeout and ten retries.

### Evaluation contract

The synthetic evaluation fixture is `tests/evaluation/pii_detection_cases.json`.
Each case has `name`, `text`, and expected entities with `entity_type`,
`value`, `start`, and `end`. Evaluation keys are `(entity_type, start, end)`;
values and scores do not affect matching. Empty detected and expected sets
produce precision `1.0`, recall `1.0`, and F1 `1.0`; when only one set is
empty, the corresponding standard zero-denominator rule is used. The current
fixture covers email, Swiss AHV, IBAN, phone, UID, and a no-PII case.
