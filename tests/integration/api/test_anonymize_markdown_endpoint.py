from uuid import uuid4

from fastapi.testclient import TestClient

from privacy_engine.api.dependencies import get_anonymize_markdown_use_case
from privacy_engine.application.exceptions import InvalidInputError
from privacy_engine.application.markdown_models import (
    MarkdownAnonymizationResult,
    MarkdownDocument,
)
from privacy_engine.main import create_app


class InvalidInputUseCase:
    def execute(
        self,
        document: MarkdownDocument,
        language: str | None = None,
    ):
        raise InvalidInputError(
            "Unable to process anonymization input"
        )


class FakeUseCase:
    def execute(
        self,
        document: MarkdownDocument,
        language: str | None = None,
    ) -> MarkdownAnonymizationResult:
        return MarkdownAnonymizationResult(
            document_id=uuid4(),
            filename=document.filename,
            language="en",
            safe_markdown=document.content,
            is_safe_for_ai=True,
            entity_count=0,
            entities=(),
            mappings=(),
        )


class EmailFakeUseCase:
    def execute(
        self,
        document: MarkdownDocument,
        language: str | None = None,
    ) -> MarkdownAnonymizationResult:
        from privacy_engine.application.models import (
            AnonymizationMapping,
        )
        from privacy_engine.domain.entities import PIIEntity

        return MarkdownAnonymizationResult(
            document_id=uuid4(),
            filename=document.filename,
            language="en",
            safe_markdown="Email: [EMAIL_001]",
            is_safe_for_ai=False,
            entity_count=1,
            entities=(
                PIIEntity(
                    entity_type="EMAIL",
                    value="adam@example.com",
                    start=7,
                    end=23,
                ),
            ),
            mappings=(
                AnonymizationMapping(
                    entity_type="EMAIL",
                    original_value="adam@example.com",
                    replacement_value="[EMAIL_001]",
                ),
            ),
        )


def test_anonymize_markdown_endpoint_returns_safe_markdown() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_markdown_use_case
    ] = lambda: EmailFakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize/markdown",
            json={
                "filename": "notes.md",
                "markdown": "Email: adam@example.com",
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["safe_markdown"] == "Email: [EMAIL_001]"
    assert body["entity_count"] == 1
    assert body["is_safe_for_ai"] is False
    assert body["filename"] == "notes.md"
    assert body["language"] == "en"
    assert len(body["mappings"]) == 1
    assert "document_id" in body


def test_anonymize_markdown_endpoint_keeps_markdown_without_pii() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_markdown_use_case
    ] = lambda: FakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize/markdown",
            json={
                "filename": "notes.md",
                "markdown": "# Hello world",
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["safe_markdown"] == "# Hello world"
    assert body["entity_count"] == 0
    assert body["is_safe_for_ai"] is True
    assert body["mappings"] == []


def test_anonymize_markdown_endpoint_requires_markdown() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_markdown_use_case
    ] = lambda: FakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize/markdown",
            json={"filename": "notes.md"},
        )

    assert response.status_code == 422


def test_anonymize_markdown_endpoint_rejects_empty_markdown() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_markdown_use_case
    ] = lambda: FakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize/markdown",
            json={"filename": "notes.md", "markdown": ""},
        )

    assert response.status_code == 422


def test_anonymize_markdown_endpoint_rejects_whitespace_markdown() -> (
    None
):
    app = create_app()

    app.dependency_overrides[
        get_anonymize_markdown_use_case
    ] = lambda: FakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize/markdown",
            json={"filename": "notes.md", "markdown": "   "},
        )

    assert response.status_code == 422


def test_anonymize_markdown_endpoint_requires_filename() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_markdown_use_case
    ] = lambda: FakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize/markdown",
            json={"markdown": "Hello"},
        )

    assert response.status_code == 422


def test_anonymize_markdown_endpoint_rejects_empty_filename() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_markdown_use_case
    ] = lambda: FakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize/markdown",
            json={"filename": "  ", "markdown": "Hello"},
        )

    assert response.status_code == 422


def test_anonymize_markdown_defaults_to_no_persistence() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_markdown_use_case
    ] = lambda: FakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize/markdown",
            json={"filename": "notes.md", "markdown": "Hello"},
        )

    assert response.status_code == 200


def test_anonymize_markdown_can_enable_persistence() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_markdown_use_case
    ] = lambda: FakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize/markdown",
            json={
                "filename": "notes.md",
                "markdown": "Hello",
                "persist": True,
            },
        )

    assert response.status_code == 200


def test_anonymize_markdown_returns_400_for_invalid_application_input() -> (
    None
):
    app = create_app()

    app.dependency_overrides[
        get_anonymize_markdown_use_case
    ] = lambda: InvalidInputUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize/markdown",
            json={
                "filename": "notes.md",
                "markdown": "valid input",
                "persist": False,
            },
        )

    assert response.status_code == 400

    assert response.json() == {
        "detail": "Unable to process anonymization input"
    }
