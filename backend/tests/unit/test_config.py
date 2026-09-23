import pytest
from pydantic import ValidationError

from app.core.config import Settings


def configured(**overrides):
    values = {
        "database_url": "postgresql+psycopg://app:secret@db.internal/arbitra",
        "frontend_url": "https://arbitra.example.edu.br",
        "cookie_secure": True,
        "_env_file": None,
    }
    return Settings(**(values | overrides))


def test_frontend_url_is_normalized_to_an_origin():
    settings = configured(frontend_url="https://arbitra.example.edu.br/")
    assert settings.frontend_url == "https://arbitra.example.edu.br"


@pytest.mark.parametrize(
    "frontend_url",
    [
        "arbitra.example.edu.br",
        "https://user:password@arbitra.example.edu.br",
        "https://arbitra.example.edu.br/app",
        "https://arbitra.example.edu.br?source=test",
    ],
)
def test_frontend_url_rejects_values_that_are_not_origins(frontend_url):
    with pytest.raises(ValidationError):
        configured(frontend_url=frontend_url)


def test_production_requires_https_and_secure_cookies():
    with pytest.raises(ValidationError):
        configured(
            environment="production",
            frontend_url="http://arbitra.example.edu.br",
            cookie_secure=False,
        )


def test_cross_site_cookie_requires_https():
    with pytest.raises(ValidationError):
        configured(cookie_secure=False, cookie_samesite="none")


@pytest.mark.parametrize(
    ("field", "value"),
    [("session_hours", 0), ("pool_size", 0), ("pool_overflow", 21)],
)
def test_operational_limits_are_bounded(field, value):
    with pytest.raises(ValidationError):
        configured(**{field: value})


def test_database_driver_is_explicit():
    with pytest.raises(ValidationError):
        configured(database_url="sqlite:///arbitra.db")


def test_production_requires_email_delivery_configuration():
    with pytest.raises(ValidationError):
        configured(environment="production")
    configured(
        environment="production",
        smtp_host="smtp.example.edu.br",
        smtp_from="IF-Arbitra <noreply@example.edu.br>",
    )


def test_database_url_must_be_explicit(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
