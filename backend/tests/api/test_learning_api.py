import os
import uuid

import bcrypt
import pytest

from backend.app import create_app
from backend.config import TestConfig
from backend.extensions import mongo


class IntegrationConfig(TestConfig):
    MONGO_URI = os.getenv("TEST_MONGO_URI", "mongodb://localhost:27017/edubridge_test?serverSelectionTimeoutMS=1000")


@pytest.fixture
def api_client():
    app = create_app(IntegrationConfig)
    with app.app_context():
        try:
            mongo.cx.admin.command("ping")
        except Exception as error:
            pytest.skip(f"MongoDB is unavailable: {error}")
        mongo.cx.drop_database(mongo.db.name)
        mongo.db.users.create_index("email", unique=True)
        mongo.db.events.create_index("event_id", unique=True)
        password_hash = bcrypt.hashpw(b"EduBridgeTest!2026", bcrypt.gensalt()).decode()
        teacher_id = mongo.db.users.insert_one({"name": "Test Teacher", "email": "teacher@example.com", "password_hash": password_hash, "role": "teacher", "active": True, "class_id": "class-a"}).inserted_id
        student_id = mongo.db.users.insert_one({"name": "Test Student", "email": "student@example.com", "password_hash": password_hash, "role": "student", "active": True, "language": "ta", "class_id": "class-a"}).inserted_id
        parent_id = mongo.db.users.insert_one({"name": "Test Parent", "email": "parent@example.com", "password_hash": password_hash, "role": "parent", "active": True, "linked_students": [str(student_id)]}).inserted_id
        mongo.db.classes.insert_one({"class_id": "class-a", "name": "Test class", "teacher_id": str(teacher_id), "student_ids": [str(student_id)]})
        mongo.db.curriculum.insert_one({
            "concept_id": "test-concept", "subject": "Mathematics", "chapter": "Algebra", "lesson": "Variables",
            "title": {"ta": "மாறிகள்", "en": "Variables"}, "review_status": "approved",
            "content": {"ta": {f"s{stage}": "Tamil lesson" for stage in range(5)}, "en": {f"s{stage}": "English lesson" for stage in range(5)}},
            "keywords": [{"ta": "மாறி", "en": "variable"}],
            "quiz": [{"q_id": "q1", "kind": "concept", "question": {"ta": "x மதிப்பு?", "en": "Value of x?"}, "options": {"ta": ["7", "8"], "en": ["7", "8"]}, "answer": {"ta": "7", "en": "7"}}],
        })
    yield app.test_client(), {"teacher": str(teacher_id), "student": str(student_id), "parent": str(parent_id)}
    with app.app_context():
        mongo.cx.drop_database(mongo.db.name)


def _token(client, email):
    response = client.post("/api/auth/login", json={"email": email, "password": "EduBridgeTest!2026"})
    assert response.status_code == 200
    return response.json["access_token"]


def test_answer_is_scored_server_side_and_duplicate_is_idempotent(api_client):
    client, _ids = api_client
    token = _token(client, "student@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    event_id = str(uuid.uuid4())
    payload = {"event_id": event_id, "concept_id": "test-concept", "stage": 0, "q_id": "q1", "selected_option": "7", "time_ms": 1200}

    first = client.post("/api/learn/answer", json=payload, headers=headers)
    duplicate = client.post("/api/learn/answer", json=payload, headers=headers)

    assert first.status_code == 200
    assert first.json["correct"] is True
    assert first.json["M"] > 0.30
    assert duplicate.status_code == 409
    with client.application.app_context():
        assert mongo.db.events.count_documents({"event_id": event_id}) == 1


def test_stage_mismatch_is_logged_but_does_not_change_mastery(api_client):
    client, _ids = api_client
    token = _token(client, "student@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/learn/answer", json={
        "event_id": str(uuid.uuid4()), "concept_id": "test-concept", "stage": 2,
        "q_id": "q1", "selected_option": "7", "time_ms": 100,
    }, headers=headers)

    assert response.status_code == 422
    with client.application.app_context():
        assert mongo.db.events.find_one({"valid": False, "reason": "stage_mismatch"})
        assert mongo.db.mastery.count_documents({}) == 0


def test_missing_event_field_is_stored_as_invalid(api_client):
    client, _ids = api_client
    token = _token(client, "student@example.com")
    event_id = str(uuid.uuid4())
    response = client.post("/api/learn/answer", json={
        "event_id": event_id, "concept_id": "test-concept", "stage": 0,
        "q_id": "q1", "selected_option": "7",
    }, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 422
    with client.application.app_context():
        assert mongo.db.events.find_one({"event_id": event_id, "valid": False, "reason": "missing_fields:time_ms"})
        assert mongo.db.mastery.count_documents({}) == 0


def test_option_not_offered_is_rejected_and_logged(api_client):
    client, _ids = api_client
    token = _token(client, "student@example.com")
    event_id = str(uuid.uuid4())
    response = client.post("/api/learn/answer", json={
        "event_id": event_id, "concept_id": "test-concept", "stage": 0,
        "q_id": "q1", "selected_option": "not-an-option", "time_ms": 100,
    }, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 422
    with client.application.app_context():
        assert mongo.db.events.find_one({"event_id": event_id, "valid": False, "reason": "invalid_option"})
        assert mongo.db.mastery.count_documents({}) == 0


def test_parent_cannot_access_teacher_route_and_only_sees_linked_child(api_client):
    client, ids = api_client
    student_token = _token(client, "student@example.com")
    lesson_response = client.get("/api/learn/test-concept", headers={"Authorization": f"Bearer {student_token}"})
    parent_token = _token(client, "parent@example.com")
    headers = {"Authorization": f"Bearer {parent_token}"}

    forbidden = client.get("/api/teacher/class/class-a/summary", headers=headers)
    child_view = client.get(f"/api/parent/child/{ids['student']}", headers=headers)
    other_child = client.get(f"/api/parent/child/{ids['teacher']}", headers=headers)

    assert forbidden.status_code == 403
    assert lesson_response.status_code == 200
    assert child_view.status_code == 200
    assert "events" not in child_view.json
    assert child_view.json["recent_activity"]["last_lesson"]
    assert other_child.status_code == 404


def test_deactivated_account_cannot_reuse_existing_token(api_client):
    client, ids = api_client
    token = _token(client, "student@example.com")
    with client.application.app_context():
        from bson import ObjectId

        mongo.db.users.update_one({"_id": ObjectId(ids["student"])}, {"$set": {"active": False}})
    response = client.get("/api/concepts", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401