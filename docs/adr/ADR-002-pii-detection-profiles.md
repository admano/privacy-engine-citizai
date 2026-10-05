# ADR-002: Local ONNX NER as the only active PII provider

## Status

Accepted for the regenerated implementation.

## Context

The API must detect names, organizations, and locations without transmitting
input to an external service. The project contains a local token-classification
model under `pii-ner/`. Multiple active providers make the running profile
ambiguous and can produce duplicate or conflicting detections.

## Decision

`OnnxNerPIIProvider` is the sole provider returned by
`privacy_engine.api.dependencies._build_pii_provider`. It loads only from the
local `pii-ner/` directory with `local_files_only=True`, so inference never
downloads a model at request time. It maps model labels `PER`, `LOC`, and `ORG`
to the domain names `PERSON`, `LOCATION`, and `ORGANIZATION`.

The default profile must not instantiate `CompositePIIProvider`,
`RuleBasedPIIProvider`, `RegexPIIProvider`, or `PresidioPIIProvider`. Such
adapters may remain available for future work, but changing the active profile
requires a new ADR.

Language resolution still resolves `de`, `fr`, `it`, or `en` before detection.
The local multilingual ONNX model may ignore this input for inference.

## Reproduction requirements

The following are mandatory application dependencies in
`[project.dependencies]`, not optional extras:

- `onnxruntime`
- `optimum[onnxruntime]`
- `transformers`

`requirements.txt` must install the application and development dependencies
with `-e .[dev]`, so `python -m pip install -r requirements.txt` installs the
complete local API runtime. Model configuration and tokenizer files are version
controlled. The large `pii-ner/model.onnx` weight file is supplied locally and
ignored by Git; startup must report a clear error if it is unavailable.

## Verification

Tests must assert that `_build_pii_provider()` returns an
`OnnxNerPIIProvider`, not a composite. Integration coverage must call
`POST /api/v1/privacy/anonymize` using the real bundled model and verify that
the resulting entities originate from this provider alone.
