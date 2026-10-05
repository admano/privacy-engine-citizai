Review the existing implementation of `ai-privacy-engine-v2` against the newly reorganized documentation under `docs_new/`.

Your task is to make the codebase conform to the architecture, specifications, and slices defined in `docs_new/` while preserving the existing product behavior and keeping the complete test suite green.

Important:

This is a controlled architecture-alignment/refactoring task, not a redesign.

\## Primary Goal

Bring the current implementation into alignment with:

\- `docs_new/adr/`

\- `docs_new/specs/`

\- `docs_new/slices/`

The final system must still provide the same functional capabilities and project goals as before.

Existing working behavior must not be broken.

\## Before changing anything

1\. Read `AGENTS.md`.

2\. Read all relevant files in `docs_new/`.

3\. Inspect the current source code and test suite.

4\. Compare the implementation against the new documentation.

5\. Identify mismatches before editing code.

Do not start coding immediately.

\## Step 1 — Gap Analysis Only

First produce a concise implementation gap analysis.

For every relevant requirement in `docs_new/`, classify the current code as:

\- ALIGNED — already follows the new docs

\- NEEDS ENHANCEMENT — behavior exists but structure/design should improve

\- NEEDS CHANGE — implementation conflicts with the new docs

\- MISSING — required implementation does not exist

\- OBSOLETE — code exists but is no longer needed according to `docs_new/`

For every mismatch show:

\- requirement / architecture rule

\- current implementation

\- proposed change

\- affected files

\- risk to existing behavior

\- tests that protect the behavior

Then STOP and wait for my approval.

Do not edit any files during Step 1.

\---

\## Step 2 — Implementation after approval

After I approve the gap analysis, update the code incrementally.

Follow these rules strictly.

\### Preserve behavior

The existing product purpose and functional result must stay the same.

Do not intentionally change:

\- existing endpoint behavior unless `docs_new/` explicitly requires it

\- anonymization output semantics

\- multilingual support

\- PII detection behavior

\- Markdown behavior

\- persistence semantics

\- document correlation behavior

\- error response semantics

\- database transaction behavior

If a documented architecture improvement can be implemented without changing public behavior, prefer that approach.

\### Architecture alignment

Make the implementation follow the boundaries described in `docs_new/`.

In particular, preserve or enforce clean separation between:

\`\`\`text

API

↓

Application

↓

Domain contracts

↑

Infrastructure adapter