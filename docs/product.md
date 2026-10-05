# citizai-privacy

## Purpose

citizai-privacy detects personally identifiable information (PII) before text
or Markdown is sent to an AI system. It returns anonymized content, detected
entities, and replacement mappings under a generated document ID.

## Capabilities

- Plain-text and Markdown anonymization.
- German, French, Italian, and English language resolution.
- Numbered replacement tokens and entity/mapping metadata.
- Optional PostgreSQL persistence when `persist=true`.
- HTTP endpoints under `/api/v1`.
- Local PII detection adapters and a bundled ONNX NER model.

The desired default detection profile and its reproducible runtime are defined
by [ADR-002](adr/ADR-002-pii-detection-profiles.md) and
[ADR-004](adr/ADR-004-one-command-local-runtime.md). Any implementation
change from the current profile must follow those ADRs through a new slice.

## Non-goals

The project does not currently provide authentication, authorization, a web
frontend, mapping retrieval or de-anonymization, audit logging, background
jobs, LLM integration, or distributed deployment.
