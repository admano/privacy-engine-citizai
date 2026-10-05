from fastapi.testclient import TestClient

from privacy_engine.main import create_app


def test_request_id_is_returned() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/health",
            headers={
                "X-Request-ID": "test-request-123"
            },
        )

    assert response.status_code == 200
    assert (
        response.headers["X-Request-ID"]
        == "test-request-123"
    )


def test_request_id_is_generated() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/health"
        )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]