# AI Privacy Engine

Detects and anonymizes personally identifiable information (PII) before
content is sent to AI systems. See [docs/README.md](docs/README.md) for the
canonical product, architecture, runtime, testing, and security documentation.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"

cp .env.example .env
docker compose up -d
alembic upgrade head
```

The application uses lightweight structured PII detection as described in
`docs/adr/ADR-002-pii-detection-profiles.md`.

## Running

```bash
uvicorn privacy_engine.main:app --reload
```

## Tests

```bash
pytest
```

Integration tests under `tests/integration/database` and the `persist`
paths of `tests/integration/api` require the Postgres container from
`compose.yaml` to be running.
