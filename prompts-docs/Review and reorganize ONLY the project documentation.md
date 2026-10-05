Review and reorganize ONLY the project documentation for the existing

ai-privacy-engine-v2 project.

Your task is NOT to redesign the application and NOT to change implementation code.

Your goal is to make the documentation:

\- clearer

\- more consistent

\- easier to read

\- easier for a new developer or AI agent to understand

\- less repetitive

\- better structured

\- smaller in number of files where reasonable

\- still complete enough to preserve all important architectural and feature decisions

Important rules:

1\. Read [AGENTS.md](http://AGENTS.md) first.

2\. Read the consolidated architecture and behaviour documentation under
   `docs/adr/`.

3\. Do not delete any information that is still relevant to the current project.

4\. Do not remove architectural decisions that explain why the system works the way it does.

5\. Do not remove important constraints, security rules, persistence semantics, error-handling rules, language support, Markdown behavior, or testing expectations.

6\. Do not invent new architecture unless required to resolve an obvious documentation contradiction.

7\. Do not modify production code.

8\. Do not implement features.

9\. Do not change public API behavior.

10\. Do not change database behavior.

11\. Do not change tests.

12\. Documentation changes only.

Main objective:

Reduce unnecessary fragmentation.

If multiple ADRs, specs, or slices describe the same concern and can be safely combined,

merge them into a smaller number of well-defined documents.

Prefer fewer comprehensive files over many tiny documents, but do not create giant

unstructured files.

The final documentation should be organized so that somebody new to the project can

understand the system in this order:

1\. What the product does

2\. Overall architecture

3\. Core anonymization flow

4\. PII provider architecture

5\. Multilingual support

6\. Entity normalization/resolution

7\. Persistence and document correlation

8\. API behavior and error handling

9\. Markdown anonymization

10\. Testing/evaluation strategy

11\. Remaining limitations / security considerations

Documentation principles:

\- Remove duplicated explanations.

\- Merge documents that represent one architectural concern.

\- Preserve historical decisions only when they are still relevant to understanding the current architecture.

\- If an old decision has been superseded, keep the relevant reasoning in a concise "Superseded / Evolution" section instead of keeping multiple confusing documents.

\- Prefer references between documents instead of repeating the same content.

\- Use consistent terminology everywhere.

\- Standardize names such as:

  - PIIProvider

  - AnonymizeText

  - AnonymizeMarkdown

  - EntityResolver

  - TokenAnonymizer

  - LanguageResolver

  - MappingRepository

  - SQLAlchemyMappingRepository

  - document_id

\- Make sure Markdown and plain-text anonymization are clearly presented as two adapters/features using the same privacy core, not two separate engines.

For ADRs:

Review all current ADRs and identify which ones can be merged.

A good target is a small set of larger architectural ADRs such as:

\- Architecture and dependency boundaries

\- PII detection and anonymization pipeline

\- Persistence and transaction model

\- API and error-handling model

\- Multilingual detection and provider strategy

\- Markdown anonymization strategy

This is only a suggested grouping. Use the existing project content to decide the best final structure.

For Specs:

Review all specs and merge where they belong to the same functional area.

Prefer feature-oriented specs such as:

\- Core text anonymization

\- Mapping persistence / retrieval

\- Multilingual PII detection

\- Markdown anonymization

Avoid having separate specs for tiny implementation details.

For Slices:

Slices should remain implementation-oriented, but reduce unnecessary duplication.

Group already completed slices where several small slices together represent one finished capability.

For example, several historical slices about:

\- DB runtime

\- SQLAlchemy repository

\- Alembic

\- transaction handling

could be summarized into one completed persistence capability document.

Likewise, several slices about:

\- Presidio

\- Swiss recognizers

\- context confidence

\- entity normalization

\- evaluation

may be reorganized into a clearer detection/evaluation capability grouping.

Do NOT lose the implementation history entirely.

For completed work, preserve:

\- goal

\- key decision

\- important files/components

\- acceptance criteria

\- important tests

\- relevant caveats

but remove repeated implementation instructions that no longer add value.

For active or future slices:

Keep them separate if they still represent work that has not yet been completed.

Current Markdown feature documentation must remain complete and clearly represented.

Specifically preserve all relevant Markdown requirements:

\- POST /api/v1/privacy/anonymize/markdown

\- optional language

\- automatic language detection

\- preserve Markdown structure

\- anonymize headings, paragraphs, lists, blockquotes, tables, link labels

\- do not anonymize fenced code blocks

\- do not anonymize inline code

\- do not anonymize link destinations

\- do not anonymize image destinations

\- one document_id per Markdown operation

\- aggregate mappings/entities

\- persist mappings through existing MappingRepository

\- no SQLAlchemy in application/domain

\- no persistence directly in FastAPI route

Security content must be preserved:

\- original PII mappings are sensitive

\- do not log request bodies

\- do not log Markdown bodies

\- do not log original PII

\- plaintext mapping storage is currently development-oriented and not considered production-secure unless explicitly documented otherwise

Multilingual content must remain clear:

Supported languages:

\- de

\- fr

\- it

\- en

Flow:

explicit language if provided

otherwise LanguageResolver / language detector

then pass resolved language to providers

Also preserve that:

\- application does not depend on Lingua

\- Presidio receives the resolved language

\- concrete NLP/model setup belongs to infrastructure

Deliverables:

First, do NOT modify anything.

Step 1:

Analyze the current documentation and produce a proposed reorganization plan.

Show:

\- current file

\- proposed action:

  - keep

  - merge

  - rename

  - archive/supersede

\- target document

\- reason

Then propose the final docs tree.

Example:

docs/

├── [product.md](http://product.md)

├── architecture/

│   ├── [architecture.md](http://architecture.md)

│   ├── [pii-pipeline.md](http://pii-pipeline.md)

│   ├── [persistence.md](http://persistence.md)

│   ├── [multilingual.md](http://multilingual.md)

│   └── [markdown.md](http://markdown.md)

├── specs/

│   ├── [text-anonymization.md](http://text-anonymization.md)

│   ├── [mapping-persistence.md](http://mapping-persistence.md)

│   └── [markdown-anonymization.md](http://markdown-anonymization.md)

└── slices/

    ├── completed/

    └── active/

This is only an example.

Choose the structure that best fits the actual documentation.

Important:

Prefer the minimum number of files that still gives good readability.

Do not merge unrelated concepts just to reduce file count.

After presenting the proposed structure, STOP.

Wait for my approval before changing any documentation.

After I approve:

Step 2:

Perform the documentation-only refactor.

When rewriting:

\- keep concise sections

\- use consistent headings

\- remove repeated text

\- preserve all important decisions

\- preserve links/references where possible

\- update references to renamed/merged documents

\- do not leave broken references

\- do not create duplicate content

\- do not silently remove relevant information

At the end provide:

1\. Files removed

2\. Files merged

3\. Files renamed

4\. Files created

5\. Final documentation tree

6\. Important information preserved

7\. Any contradictions found in old docs

8\. Any content intentionally marked as superseded

9\. Confirmation that no application code was changed

10\. Suggested Git commit message

Start now with STEP 1 ONLY:

analyze the current docs and propose the reorganization plan.

Do not edit any files yet.
