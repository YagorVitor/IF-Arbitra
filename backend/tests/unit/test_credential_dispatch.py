import httpx
import pytest
from pydantic import SecretStr, ValidationError

from app.api.schemas.users import UserInput
from app.core.config import Settings
from app.core.errors import DomainError
from app.services import credential_dispatch
from app.services.credential_dispatch import PASSWORD_ALPHABET, PASSWORD_LENGTH, new_password
from app.services.credential_email import credential_message


def test_student_input_uses_email_as_the_only_identifier():
    student = UserInput(name="Aluno Novo", email="Aluno@Example.org")
    assert str(student.email) == "Aluno@example.org"
    with pytest.raises(ValidationError):
        UserInput(name="Aluno Novo", email="invalid")
    with pytest.raises(ValidationError):
        UserInput(name="Aluno Novo", email="aluno@example.org", login="aluno-01")
    with pytest.raises(ValidationError):
        UserInput(name="Aluno Novo", email="aluno@example.org", password="bypass")


def test_random_passwords_have_the_same_length_and_unambiguous_alphabet():
    passwords = [new_password() for _ in range(100)]
    assert len(set(passwords)) == 100
    assert PASSWORD_LENGTH == 8
    assert all(len(password) == PASSWORD_LENGTH for password in passwords)
    assert all(set(password) <= set(PASSWORD_ALPHABET) for password in passwords)


def test_resend_message_contains_rendered_email_and_uses_secret_key(monkeypatch):
    config = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://test:test@localhost/arbitra_test",
        resend_api_key=SecretStr("re_test_secret"),
        resend_from="IF-Arbitra <onboarding@resend.dev>",
    )
    message = credential_message(
        name="Capitã de Teste",
        email="capita@example.org",
        password="senha-de-teste",
        frontend_url="https://if-arbitra-frontend.vercel.app",
        sender=config.resend_from,
    )
    calls = []

    class Response:
        def raise_for_status(self):
            return None

    monkeypatch.setattr(credential_dispatch, "settings", lambda: config)
    monkeypatch.setattr(
        credential_dispatch.httpx,
        "post",
        lambda *args, **kwargs: calls.append((args, kwargs)) or Response(),
    )

    credential_dispatch._send_message(message)

    args, kwargs = calls[0]
    assert args == ("https://api.resend.com/emails",)
    assert kwargs["headers"] == {"Authorization": "Bearer re_test_secret"}
    assert kwargs["json"]["to"] == ["capita@example.org"]
    assert kwargs["json"]["from"] == config.resend_from
    assert "Capitã de Teste" in kwargs["json"]["text"]
    assert "Capitã de Teste" in kwargs["json"]["html"]


def test_resend_http_failure_becomes_safe_email_error(monkeypatch):
    config = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://test:test@localhost/arbitra_test",
        resend_api_key=SecretStr("re_test_secret"),
        resend_from="onboarding@resend.dev",
    )
    message = credential_message(
        name="Capitã de Teste",
        email="capita@example.org",
        password="senha-de-teste",
        frontend_url="https://if-arbitra-frontend.vercel.app",
        sender=config.resend_from,
    )

    def fail(*args, **kwargs):
        request = httpx.Request("POST", "https://api.resend.com/emails")
        response = httpx.Response(401, request=request)
        raise httpx.HTTPStatusError("unauthorized", request=request, response=response)

    monkeypatch.setattr(credential_dispatch, "settings", lambda: config)
    monkeypatch.setattr(credential_dispatch.httpx, "post", fail)

    with pytest.raises(DomainError, match="Falha no envio") as error:
        credential_dispatch._send_message(message)
    assert error.value.code == "EMAIL_UNAVAILABLE"
