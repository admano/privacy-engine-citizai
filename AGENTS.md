# AI Privacy Engine - Engineering Instructions

## Project purpose

This project implements a privacy engine that detects and anonymizes
personally identifiable information before content is sent to AI systems.

## Engineering workflow

For significant changes use:

ADR → Specification → Implementation Slice → Tests → Implementation → Review

Do not implement major architectural changes without documenting the decision.

## Architecture principles

- Domain logic must remain independent from web frameworks.
- Domain logic must remain independent from database frameworks.
- External PII detection engines must be replaceable.
- Infrastructure details must not leak into the domain.
- Prefer dependency injection over global state.
- Prefer explicit interfaces over hidden dependencies.
- Keep modules small and focused.

## Development rules

- Use Python type hints.
- New business logic requires unit tests.
- Avoid unrelated refactoring.
- Do not introduce dependencies without justification.
- Prefer simple implementations.
- Keep public interfaces small.
- Existing tests must remain green.

## Agent rules

Before implementing a task:

1. read relevant ADRs,
2. read the feature specification,
3. inspect existing tests,
4. identify the affected module,
5. implement only the requested slice.

Do not expand scope without justification.
