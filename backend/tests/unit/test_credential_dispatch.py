import pytest
from pydantic import ValidationError

from app.api.schemas.users import UserInput
from app.services.credential_dispatch import PASSWORD_ALPHABET, PASSWORD_LENGTH, new_password


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
