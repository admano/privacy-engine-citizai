# Testing and evaluation

`AGENTS.md` is authoritative: new business logic requires unit tests, existing
tests must remain green, and changes must stay within the requested slice.

| Directory | Scope |
|---|---|
| `tests/unit/` | Domain, application, API, and infrastructure units using fakes where practical. |
| `tests/integration/` | Real component integration, FastAPI requests, Markdown flow, and PostgreSQL persistence. |
| `tests/evaluation/` | Synthetic PII fixtures and the exact-span detection-quality evaluator. |

Run the suite with:

```bash
pytest
pytest tests/unit
pytest tests/integration
```

Database integration tests require the PostgreSQL service in `compose.yaml` and
the current Alembic migration head. The evaluator uses only synthetic examples
from `tests/evaluation/pii_detection_cases.json` and compares exact
`(entity_type, start, end)` tuples to report precision, recall, and F1.
