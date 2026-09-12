import pytest
from sqlalchemy.exc import OperationalError, TimeoutError

from app.main import app


@pytest.fixture(autouse=True)
def audit_without_database(monkeypatch):
    monkeypatch.setattr("app.api.middleware.independent", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.api.errors.independent", lambda *args, **kwargs: None)


def test_chunked_body_is_bounded_before_parsing(client):
    response = client.post(
        "/api/auth/login", content=iter([b"x" * 32000, b"x" * 32000, b"x" * 2000])
    )
    assert response.status_code == 413
    assert response.json()["code"] == "PAYLOAD_TOO_LARGE"
    assert response.headers["X-Request-ID"] == response.json()["request_id"]
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"


def test_small_stream_is_replayed_to_pydantic(client):
    response = client.post("/api/auth/login", content=iter([b'{"login":', b'"x"}']))
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_INPUT"


@pytest.mark.parametrize("length,status", [("65537", 413), ("-1", 400), ("abc", 400)])
def test_invalid_content_length(client, length, status):
    response = client.post("/api/auth/login", content=b"", headers={"Content-Length": length})
    assert response.status_code == status


@pytest.mark.parametrize("path,method,status", [("/missing", "get", 404), ("/health", "post", 405)])
def test_http_errors_use_contract(client, path, method, status):
    response = getattr(client, method)(path)
    assert response.status_code == status
    assert set(response.json()) == {"code", "message", "request_id"}
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize(
    "failure", [OperationalError("hidden sql", {}, Exception()), TimeoutError()]
)
def test_pool_and_database_failures_are_503(client, failure):
    from app.api.dependencies import current_user

    def unavailable():
        raise failure

    app.dependency_overrides[current_user] = unavailable
    try:
        response = client.get("/api/rounds")
        assert response.status_code == 503
        assert response.json()["code"] == "SERVICE_BUSY"
        assert "hidden sql" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_database_unavailable_does_not_break_liveness(client, monkeypatch):
    def unavailable():
        raise OperationalError("hidden sql", {}, Exception())

    monkeypatch.setattr("app.api.routes.health.engine.connect", unavailable)
    assert client.get("/health").json() == {"status": "alive"}
    assert client.get("/ready").status_code == 503
