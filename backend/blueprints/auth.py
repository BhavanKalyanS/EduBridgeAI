import bcrypt
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required
from pymongo.errors import DuplicateKeyError
from pydantic import ValidationError

from backend.extensions import limiter, mongo
from backend.schemas.requests import LoginRequest, StudentRegistrationRequest
from backend.services.authz import current_user, public_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/auth/register")
@limiter.limit("5 per hour")
def register():
    try:
        payload = StudentRegistrationRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return jsonify({"error": {"code": "validation_error", "message": "Invalid student details", "fields": error.errors(include_input=False)}}), 422

    email = payload.email.lower()
    mongo.db.users.create_index("email", unique=True)
    if mongo.db.users.find_one({"email": email}):
        return jsonify({"error": {"code": "email_exists", "message": "An account with this email already exists"}}), 409

    user = {
        "name": payload.name,
        "email": email,
        "password_hash": bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode(),
        "role": "student",
        "language": payload.language,
        "board": "CBSE",
        "grade": "10",
        "class_id": None,
        "linked_students": [],
        "consent": False,
        "active": True,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        inserted = mongo.db.users.insert_one(user)
    except DuplicateKeyError:
        return jsonify({"error": {"code": "email_exists", "message": "An account with this email already exists"}}), 409
    user["_id"] = inserted.inserted_id

    token = create_access_token(identity=str(inserted.inserted_id), additional_claims={"role": "student"})
    return jsonify({"access_token": token, "user": public_user(user)}), 201


@auth_bp.post("/auth/login")
@limiter.limit("10 per minute")
def login():
    try:
        payload = LoginRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return jsonify({"error": {"code": "validation_error", "message": "Invalid login details", "fields": error.errors(include_input=False)}}), 422

    user = mongo.db.users.find_one({"email": payload.email.lower(), "active": True})
    if not user or not bcrypt.checkpw(payload.password.encode(), user["password_hash"].encode()):
        return jsonify({"error": {"code": "invalid_credentials", "message": "Email or password is incorrect"}}), 401

    token = create_access_token(
        identity=str(user["_id"]),
        additional_claims={"role": user["role"]},
    )
    mongo.db.users.update_one({"_id": user["_id"]}, {"$set": {"last_login": datetime.now(timezone.utc)}})
    return jsonify({"access_token": token, "user": public_user(user)})


@auth_bp.get("/auth/me")
@jwt_required()
def me():
    user = current_user()
    if user is None:
        return jsonify({"error": {"code": "user_unavailable", "message": "This account is unavailable"}}), 401
    return jsonify({"user": public_user(user)})