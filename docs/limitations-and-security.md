# Limitations and security

## Persistence is not production-ready

`anonymization_mapping.original_value` stores sensitive input in plaintext.
Before production use, define encryption, access control, retention, deletion,
key management, and whether de-anonymization should exist. No mapping retrieval
or de-anonymization capability is currently implemented.

## Logging and API errors

Request bodies, Markdown content, mappings, and original PII values must not be
logged. Database failures return a generic `503`; internal database details
must remain in protected logs only. See
[ADR-003](adr/ADR-003-delivery-persistence-and-markdown.md).

## Detection and Markdown limits

NER can misclassify short or structural text. One resolved language is used for
each request, so mixed-language documents are not supported. Markdown is
processed per eligible line; entities spanning manual line wraps can be missed.
The regex Markdown processor protects code, link destinations, and reference
definitions and is not a complete CommonMark parser.

## Performance

Detection and entity resolution are CPU-bound and are offloaded from the API
event loop where applicable. Entity-overlap resolution is quadratic in the
number of detected entities and must be revisited for very large documents.
