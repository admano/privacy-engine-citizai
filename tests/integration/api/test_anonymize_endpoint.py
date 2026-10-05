import logging
from uuid import uuid4

from fastapi.testclient import TestClient

from privacy_engine.api.dependencies import get_anonymize_text_use_case
from privacy_engine.application.exceptions import (
    DatabaseUnavailableError,
    InvalidInputError,
)
from privacy_engine.application.models import AnonymizationResult
from privacy_engine.main import create_app


class InvalidInputUseCase:
    def execute(
        self,
        text: str,
        language: str | None = None,
    ):
        raise InvalidInputError(
            "Unable to process anonymization input"
        )


class FakeUseCase:
    def execute(
        self,
        text: str,
        language: str | None = None,
    ) -> AnonymizationResult:
        return AnonymizationResult(
            document_id=uuid4(),
            language="en",
            safe_text=text,
            entity_count=0,
            entities=(),
            mappings=(),
        )


class DatabaseUnavailableUseCase:
    def execute(
        self,
        text: str,
        language: str | None = None,
    ) -> AnonymizationResult:
        raise DatabaseUnavailableError("database password: should-not-log")


def create_test_client() -> TestClient:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_text_use_case
    ] = lambda: FakeUseCase()

    return TestClient(app)


def test_anonymize_endpoint_returns_safe_text() -> None:
    app = create_app()

    class EmailFakeUseCase:
        def execute(
            self,
            text: str,
            language: str | None = None,
        ) -> AnonymizationResult:
            from privacy_engine.application.models import (
                AnonymizationMapping,
            )
            from privacy_engine.domain.entities import PIIEntity

            return AnonymizationResult(
                document_id=uuid4(),
                language="en",
                safe_text="Email: [EMAIL_001]",
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

    app.dependency_overrides[
        get_anonymize_text_use_case
    ] = lambda: EmailFakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize",
            json={"text": "Email: adam@example.com"},
        )

    assert response.status_code == 200

    body = response.json()

    assert "[EMAIL_001]" in body["safe_text"]
    assert body["entity_count"] >= 1
    assert len(body["mappings"]) >= 1


def test_anonymize_endpoint_keeps_text_without_pii() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_text_use_case
    ] = lambda: FakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize",
            json={"text": "Hello world"},
        )

    assert response.status_code == 200

    body = response.json()

    assert body["safe_text"] == "Hello world"
    assert body["entity_count"] == 0
    assert body["mappings"] == []


def test_anonymize_endpoint_requires_text() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_text_use_case
    ] = lambda: FakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize",
            json={},
        )

    assert response.status_code == 422


def test_anonymize_endpoint_rejects_empty_text() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_text_use_case
    ] = lambda: FakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize",
            json={"text": ""},
        )

    assert response.status_code == 422


def test_anonymize_endpoint_rejects_whitespace_text() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_text_use_case
    ] = lambda: FakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize",
            json={"text": "   "},
        )

    assert response.status_code == 422


def test_anonymize_defaults_to_no_persistence() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_text_use_case
    ] = lambda: FakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize",
            json={
                "text": "Email adam@example.com"
            },
        )

    assert response.status_code == 200


def test_anonymize_does_not_persist_when_disabled() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_text_use_case
    ] = lambda: FakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize",
            json={
                "text": "Email adam@example.com",
                "persist": False,
            },
        )

    assert response.status_code == 200


def test_anonymize_can_enable_persistence() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_text_use_case
    ] = lambda: FakeUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize",
            json={
                "text": "Email adam@example.com",
                "persist": True,
            },
        )

    assert response.status_code == 200


def test_anonymize_returns_400_for_invalid_application_input() -> None:
    app = create_app()

    app.dependency_overrides[
        get_anonymize_text_use_case
    ] = lambda: InvalidInputUseCase()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/privacy/anonymize",
            json={
                "text": "valid input",
                "persist": False,
            },
        )

    assert response.status_code == 400

    assert response.json() == {
        "detail": "Unable to process anonymization input"
    }


def test_database_error_hides_exception_details_from_response_and_logs(
    caplog,
) -> None:
    app = create_app()
    app.dependency_overrides[
        get_anonymize_text_use_case
    ] = lambda: DatabaseUnavailableUseCase()

    with caplog.at_level(logging.ERROR, logger="privacy_engine.api"):
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/privacy/anonymize",
                json={"text": "valid input"},
            )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database temporarily unavailable"
    }
    assert "database password: should-not-log" not in caplog.text
    assert "database operation failed" in caplog.text
