from datetime import datetime, timezone
from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError

from backend.extensions import mongo
from backend.middleware.rbac import role_required
from backend.schemas.requests import AnswerRequest
from backend.services.authz import current_user
from backend.services.bkt import update_mastery
from backend.services.event_validator import validate_answer_event, validate_event_fields
from backend.services.settings import learning_settings
from backend.services.stage_controller import next_stage

learning_bp = Blueprint("learning", __name__)


def _record_rejected(event_id: str, user_id: str, payload: dict, reason: str) -> None:
    mongo.db.events.insert_one({
        "event_id": event_id,
        "user_id": user_id,
        "concept_id": payload.get("concept_id"),
        "stage": payload.get("stage"),
        "q_id": payload.get("q_id"),
        "valid": False,
        "reason": reason,
        "ts": datetime.now(timezone.utc),
    })


@learning_bp.post("/learn/answer")
@jwt_required()
@role_required("student")
def answer():
    raw_payload = request.get_json(silent=True) or {}
    try:
        payload = AnswerRequest.model_validate(raw_payload)
    except ValidationError as error:
        raw_event_id = raw_payload.get("event_id") if isinstance(raw_payload, dict) else None
        try:
            event_id = str(UUID(str(raw_event_id)))
        except (ValueError, TypeError, AttributeError):
            event_id = None
        if event_id:
            if mongo.db.events.find_one({"event_id": event_id}):
                return jsonify({"error": {"code": "duplicate_event_id", "message": "This answer has already been submitted"}}), 409
            complete, field_reason = validate_event_fields(raw_payload, {"event_id", "concept_id", "stage", "q_id", "selected_option", "time_ms"})
            reason = field_reason if not complete else "invalid_fields"
            try:
                _record_rejected(event_id, str(get_jwt_identity()), raw_payload, reason)
            except DuplicateKeyError:
                return jsonify({"error": {"code": "duplicate_event_id", "message": "This answer has already been submitted"}}), 409
        return jsonify({"error": {"code": "validation_error", "message": "Invalid answer payload", "fields": error.errors(include_input=False)}}), 422

    user_id = str(get_jwt_identity())
    event_id = str(payload.event_id)
    if mongo.db.events.find_one({"event_id": event_id}):
        return jsonify({"error": {"code": "duplicate_event_id", "message": "This answer has already been submitted"}}), 409

    concept = mongo.db.curriculum.find_one({"concept_id": payload.concept_id, "review_status": "approved"})
    mastery = mongo.db.mastery.find_one({"user_id": user_id, "concept_id": payload.concept_id})
    current_stage = mastery.get("stage", 0) if mastery else 0
    valid, reason = validate_answer_event(
        concept_exists=concept is not None,
        submitted_stage=payload.stage,
        current_stage=current_stage,
        event_exists=False,
    )
    question = next((item for item in (concept or {}).get("quiz", []) if item.get("q_id") == payload.q_id), None)
    if valid and question is None:
        valid, reason = False, "unknown_question"

    user = current_user()
    if valid and question is not None:
        options = question.get("options", [])
        if isinstance(options, dict):
            options = options.get(user.get("language", "ta")) or options.get("ta") or options.get("en", [])
        if payload.selected_option not in options:
            valid, reason = False, "invalid_option"

    if not valid:
        try:
            _record_rejected(event_id, user_id, raw_payload, reason or "invalid_event")
        except DuplicateKeyError:
            return jsonify({"error": {"code": "duplicate_event_id", "message": "This answer has already been submitted"}}), 409
        return jsonify({"error": {"code": reason, "message": "The answer event was rejected"}}), 422

    correct_answer = question.get("answer")
    if isinstance(correct_answer, dict):
        correct_answer = correct_answer.get(user.get("language", "ta")) or correct_answer.get("ta") or correct_answer.get("en")
    correct = str(payload.selected_option) == str(correct_answer)
    event = {
        "event_id": event_id,
        "user_id": user_id,
        "concept_id": payload.concept_id,
        "stage": payload.stage,
        "kind": question["kind"],
        "q_id": payload.q_id,
        "correct": correct,
        "selected_option": payload.selected_option,
        "time_ms": payload.time_ms,
        "ts": datetime.now(timezone.utc),
        "valid": True,
    }
    try:
        mongo.db.events.insert_one(event)
    except DuplicateKeyError:
        return jsonify({"error": {"code": "duplicate_event_id", "message": "This answer has already been submitted"}}), 409

    bkt_parameters, stage_thresholds = learning_settings()
    current_m = mastery.get("M", bkt_parameters.initial_mastery) if mastery else bkt_parameters.initial_mastery
    current_l = mastery.get("L", bkt_parameters.initial_mastery) if mastery else bkt_parameters.initial_mastery
    if question["kind"] == "keyword":
        current_l = update_mastery(current_l, correct, bkt_parameters)
    else:
        current_m = update_mastery(current_m, correct, bkt_parameters)

    recent = (mastery.get("recent", []) if mastery else []) + [int(correct)]
    recent = recent[-5:]
    decision = next_stage(current_m, current_l, recent, current_stage, stage_thresholds)
    now = datetime.now(timezone.utc)
    update = {
        "$set": {
            "user_id": user_id,
            "concept_id": payload.concept_id,
            "M": current_m,
            "L": current_l,
            "stage": decision.stage,
            "recent": recent,
            "updated_at": now,
        }
    }
    if correct:
        update["$set"]["last_correct_at"] = now
    mongo.db.mastery.update_one(
        {"user_id": user_id, "concept_id": payload.concept_id},
        update,
        upsert=True,
    )
    return jsonify({
        "correct": correct,
        "M": round(current_m, 4),
        "L": round(current_l, 4),
        "stage": decision.stage,
        "stage_changed": decision.stage_changed,
        "vocab_flag": decision.vocabulary_support,
        "stage_reason": decision.reason,
    })