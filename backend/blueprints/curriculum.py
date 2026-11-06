from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from backend.extensions import mongo
from backend.middleware.rbac import role_required
from backend.services.authz import current_user

curriculum_bp = Blueprint("curriculum", __name__)


def _stage_for(user_id: str, concept_id: str) -> dict:
    mastery = mongo.db.mastery.find_one({"user_id": user_id, "concept_id": concept_id})
    if mastery:
        return mastery
    initial_mastery = current_app.config["BKT_P0"]
    return {"M": initial_mastery, "L": initial_mastery, "stage": 0, "recent": []}


@curriculum_bp.get("/concepts")
@jwt_required()
@role_required("student")
def concepts():
    user = current_user()
    subject = request.args.get("subject")
    query = {
        "review_status": "approved",
        "grade": user.get("grade") or "10",
        "board": user.get("board") or "CBSE",
    }
    if subject:
        query["subject"] = subject

    items = []
    for concept in mongo.db.curriculum.find(query).sort([("chapter", 1), ("lesson", 1)]):
        stored_progress = mongo.db.mastery.find_one({"user_id": str(user["_id"]), "concept_id": concept["concept_id"]})
        progress = stored_progress or _stage_for(str(user["_id"]), concept["concept_id"])
        items.append({
            "concept_id": concept["concept_id"],
            "subject": concept["subject"],
            "chapter": concept["chapter"],
            "lesson": concept["lesson"],
            "title": concept.get("title", {}).get(user.get("language", "ta")) or concept.get("title", {}).get("ta", ""),
            "M": progress.get("M", 0.30),
            "L": progress.get("L", 0.30),
            "stage": progress.get("stage", 0),
            "started": stored_progress is not None,
        })
    return jsonify({"concepts": items})


@curriculum_bp.get("/learn/<concept_id>")
@jwt_required()
@role_required("student")
def lesson(concept_id: str):
    user = current_user()
    concept = mongo.db.curriculum.find_one({
        "concept_id": concept_id,
        "review_status": "approved",
        "grade": user.get("grade") or "10",
        "board": user.get("board") or "CBSE",
    })
    if concept is None:
        return jsonify({"error": {"code": "concept_not_found", "message": "Concept not found"}}), 404

    progress = _stage_for(str(user["_id"]), concept_id)
    mongo.db.users.update_one({"_id": user["_id"]}, {"$set": {"last_lesson_at": datetime.now(timezone.utc)}})
    language = user.get("language", "ta")
    stage_key = f"s{progress.get('stage', 0)}"
    localized_content = concept.get("content", {}).get(language, {})
    content = localized_content.get(stage_key) or concept.get("content", {}).get("ta", {}).get(stage_key, "Content is awaiting translation review.")
    keywords = [
        {"en": item.get("en", ""), "regional": item.get(language) or item.get("ta", "")}
        for item in concept.get("keywords", [])
    ] if progress.get("stage", 0) >= 1 else []
    questions = [
        {
            "q_id": item["q_id"],
            "kind": item["kind"],
            "question": item.get("question", {}).get(language) or item.get("question", {}).get("ta", ""),
            "options": item.get("options", {}).get(language) or item.get("options", {}).get("ta") if isinstance(item.get("options"), dict) else item.get("options", []),
        }
        for item in concept.get("quiz", [])
    ]
    return jsonify({
        "concept_id": concept_id,
            "title": concept.get("title", {}).get(language) or concept.get("title", {}).get("ta", ""),
        "stage": progress.get("stage", 0),
        "stage_note": "This stage shows the amount of English support, not English proficiency.",
        "content": content,
        "keywords": keywords,
        "quiz": questions,
    })


@curriculum_bp.get("/learn/revision")
@jwt_required()
@role_required("student")
def revision():
    user = current_user()
    user_id = str(user["_id"])
    language = user.get("language", "ta")
    items = []
    for progress in mongo.db.mastery.find({"user_id": user_id}):
        needs_revision = progress.get("M", 1) < 0.60 or progress.get("recent", [])[-3:] == [0, 0, 0]
        needs_vocabulary = progress.get("M", 0) >= 0.85 and progress.get("L", 1) < 0.70
        if not (needs_revision or needs_vocabulary):
            continue
        concept = mongo.db.curriculum.find_one({"concept_id": progress["concept_id"]})
        if concept:
            items.append({
                "concept_id": concept["concept_id"],
                "title": concept.get("title", {}).get(language, concept.get("title", {}).get("ta", "")),
                "M": progress.get("M", 0),
                "L": progress.get("L", 0),
                "stage": progress.get("stage", 0),
                "vocabulary_support": needs_vocabulary,
            })
    return jsonify({"concepts": items})