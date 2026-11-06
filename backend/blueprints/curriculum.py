from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import jwt_required
from gridfs import GridFSBucket
from gridfs.errors import NoFile
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


def _curriculum_query(user: dict, subject: str | None = None) -> dict:
    query = {
        "review_status": "approved",
        "grade": user.get("grade") or "10",
        "board": user.get("board") or "CBSE",
    }
    if mongo.db.curriculum.count_documents(query | {"source_kind": "cbse_textbook"}):
        query["source_kind"] = "cbse_textbook"
    if subject:
        query["subject"] = subject
    return query


@curriculum_bp.get("/concepts")
@jwt_required()
@role_required("student")
def concepts():
    user = current_user()
    subject = request.args.get("subject")
    query = _curriculum_query(user, subject)

    items = []
    for concept in mongo.db.curriculum.find(query).sort([("subject", 1), ("chapter_number", 1), ("chapter", 1), ("lesson", 1)]):
        stored_progress = mongo.db.mastery.find_one({"user_id": str(user["_id"]), "concept_id": concept["concept_id"]})
        progress = stored_progress or _stage_for(str(user["_id"]), concept["concept_id"])
        items.append({
            "concept_id": concept["concept_id"],
            "subject": concept["subject"],
            "chapter": concept["chapter"],
            "lesson": concept["lesson"],
            "title": concept.get("title", {}).get(user.get("language", "ta")) or concept.get("title", {}).get("ta") or concept.get("title", {}).get("en", ""),
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
    concept = mongo.db.curriculum.find_one(_curriculum_query(user) | {"concept_id": concept_id})
    if concept is None:
        return jsonify({"error": {"code": "concept_not_found", "message": "Concept not found"}}), 404

    progress = _stage_for(str(user["_id"]), concept_id)
    mongo.db.users.update_one({"_id": user["_id"]}, {"$set": {"last_lesson_at": datetime.now(timezone.utc)}})
    language = user.get("language", "ta")
    stage_key = f"s{progress.get('stage', 0)}"
    source_id = concept.get("source_id")
    source_page_count = None
    if source_id:
        source = mongo.db.textbook_sources.find_one({"source_id": source_id})
        if source is None or not source.get("text"):
            return jsonify({"error": {"code": "textbook_content_unavailable", "message": "The textbook content is temporarily unavailable"}}), 503
        content = source["text"]
        content_language = source.get("language", "en")
        source_page_count = source.get("page_count")
        textbook_source = True
    else:
        localized_content = concept.get("content", {}).get(language, {})
        content = localized_content.get(stage_key)
        content_language = language
        if not content:
            for fallback_language in ("ta", "en"):
                fallback_content = concept.get("content", {}).get(fallback_language, {}).get(stage_key)
                if fallback_content:
                    content = fallback_content
                    content_language = fallback_language
                    break
        content = content or "Content is awaiting translation review."
        textbook_source = False
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
        "title": concept.get("title", {}).get(language) or concept.get("title", {}).get("ta") or concept.get("title", {}).get("en", ""),
        "stage": progress.get("stage", 0),
        "stage_note": "This stage shows the amount of English support, not English proficiency.",
        "content": content,
        "content_language": content_language,
        "textbook_source": textbook_source,
        "source_page_count": source_page_count,
        "keywords": keywords,
        "quiz": questions,
    })


@curriculum_bp.get("/learn/<concept_id>/source.pdf")
@jwt_required()
@role_required("student")
def textbook_pdf(concept_id: str):
    user = current_user()
    concept = mongo.db.curriculum.find_one({
        "concept_id": concept_id,
        "review_status": "approved",
        "grade": user.get("grade") or "10",
        "board": user.get("board") or "CBSE",
    })
    if concept is None or not concept.get("source_id"):
        return jsonify({"error": {"code": "textbook_source_not_found", "message": "Textbook PDF not found"}}), 404

    source = mongo.db.textbook_sources.find_one({"source_id": concept["source_id"]})
    if source is None or not source.get("gridfs_file_id"):
        return jsonify({"error": {"code": "textbook_source_unavailable", "message": "The textbook PDF is temporarily unavailable"}}), 503
    try:
        pdf = GridFSBucket(mongo.db).open_download_stream(source["gridfs_file_id"])
    except NoFile:
        return jsonify({"error": {"code": "textbook_source_unavailable", "message": "The textbook PDF is temporarily unavailable"}}), 503
    return send_file(pdf, mimetype="application/pdf", as_attachment=False, download_name=source["source_file"])


@curriculum_bp.get("/learn/revision")
@jwt_required()
@role_required("student")
def revision():
    user = current_user()
    user_id = str(user["_id"])
    language = user.get("language", "ta")
    items = []
    concept_ids = [
        concept["concept_id"]
        for concept in mongo.db.curriculum.find(_curriculum_query(user), {"concept_id": 1})
    ]
    for progress in mongo.db.mastery.find({"user_id": user_id, "concept_id": {"$in": concept_ids}}):
        needs_revision = progress.get("M", 1) < 0.60 or progress.get("recent", [])[-3:] == [0, 0, 0]
        needs_vocabulary = progress.get("M", 0) >= 0.85 and progress.get("L", 1) < 0.70
        if not (needs_revision or needs_vocabulary):
            continue
        concept = mongo.db.curriculum.find_one({"concept_id": progress["concept_id"]})
        if concept:
            items.append({
                "concept_id": concept["concept_id"],
                "title": concept.get("title", {}).get(language) or concept.get("title", {}).get("ta") or concept.get("title", {}).get("en", ""),
                "M": progress.get("M", 0),
                "L": progress.get("L", 0),
                "stage": progress.get("stage", 0),
                "vocabulary_support": needs_vocabulary,
            })
    return jsonify({"concepts": items})