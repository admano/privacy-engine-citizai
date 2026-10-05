# ADR-004: One-command local runtime

## Status

Accepted for the regenerated implementation.

## Context

Recreating the service requires a Python environment, application packages,
the bundled ONNX runtime, a local PostgreSQL instance, database migrations,
and the API server. Manual sequences are error-prone: a global Python can omit
dependencies, and startup fails when `.env` has not been created.

## Decision

The implementation must expose `make run` as the supported one-command local
launch contract. It invokes a launcher that performs these steps in order:

1. Create `.venv` with Python 3.12+ when it does not exist.
2. Install `requirements.txt` with that environment's interpreter.
3. Create `.env` from `.env.example` when absent, without overwriting one.
4. Verify that `pii-ner/model.onnx` has been provisioned locally.
5. Run `docker compose up -d --wait` for PostgreSQL.
6. Run `alembic upgrade head`.
7. Start `python -m uvicorn privacy_engine.main:app` on `127.0.0.1:8000`.

The command is idempotent for existing environments and databases. Docker, a
Docker-compatible daemon, Make, Python 3.12+, and the local ONNX model weight
are explicit prerequisites. First use also needs access to the configured
Python package registry and container image registry.

## Success criteria

After Uvicorn reports startup completion, this call succeeds:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/privacy/anonymize \
  -H 'Content-Type: application/json' \
  -d '{"text":"John Smith lives in Zurich.","language":"en"}'
```

The response includes a UUID `document_id`, language `en`, anonymized text,
and entities detected by the single bundled ONNX provider. `persist` is omitted
so this smoke call does not write mappings; the database and migrations are
ready for later `persist=true` requests.

## Consequences

The launcher contains only developer composition work. Dependency declarations
remain in `pyproject.toml`, provider selection remains in
`api/dependencies.py`, and detection policy remains in ADR-002.
