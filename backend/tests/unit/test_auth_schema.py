import pytest
from pydantic import ValidationError

from backend.schemas.requests import StudentRegistrationRequest


def test_student_registration_defaults_to_tamil():
    payload = StudentRegistrationRequest.model_validate({
        "name": "New Student",
        "email": "student@example.com",
        "password": "StudentPass!2026",
    })

    assert payload.language == "ta"


def test_student_registration_rejects_role_escalation():
    with pytest.raises(ValidationError):
        StudentRegistrationRequest.model_validate({
            "name": "New Student",
            "email": "student@example.com",
            "password": "StudentPass!2026",
            "role": "admin",
        })


def test_student_registration_requires_strong_password():
    with pytest.raises(ValidationError):
        StudentRegistrationRequest.model_validate({
            "name": "New Student",
            "email": "student@example.com",
            "password": "short",
        })
