from datetime import date, datetime, timedelta, timezone

from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from pydantic import BaseModel, Field, ValidationError

from backend.extensions import mongo
from backend.middleware.rbac import role_required
from backend.services.authz import current_user

analytics_bp = Blueprint("analytics", __name__)


def _owned_class(class_id: str, teacher_id: str):
    return mongo.db.classes.find_one({"class_id": class_id, "teacher_id": teacher_id})


def _student_progress(student_ids: list[str]) -> list[dict]:
    students = []
    for student in mongo.db.users.find({"_id": {"$in": [ObjectId(value) for value in student_ids]}, "role": "student"}):
        progress = list(mongo.db.mastery.find({"user_id": str(student["_id"])}))
        students.append({
            "id": str(student["_id"]),
            "name": student["name"],
            "grade": student.get("grade"),
            "mastery": progress,
            "average_mastery": round(sum(item.get("M", 0) for item in progress) / len(progress), 3) if progress else 0,
        })
    return students


@analytics_bp.get("/teacher/class/<class_id>/summary")
@jwt_required()
@role_required("teacher")
def class_summary(class_id: str):
    teacher_id = str(get_jwt_identity())
    school_class = _owned_class(class_id, teacher_id)
    if school_class is None:
        return jsonify({"error": {"code": "class_not_found", "message": "Class not found"}}), 404
    students = _student_progress(school_class.get("student_ids", []))
    start = datetime.now(timezone.utc) - timedelta(days=7)
    weekly_activity = mongo.db.events.count_documents({"user_id": {"$in": school_class.get("student_ids", [])}, "ts": {"$gte": start}, "valid": True})
    values = [student["average_mastery"] for student in students]
    return jsonify({
        "class_id": class_id,
        "student_count": len(students),
        "average_mastery": round(sum(values) / len(values), 3) if values else 0,
        "weekly_activity": weekly_activity,
        "students": [{key: value for key, value in item.items() if key != "mastery"} for item in students],
    })


@analytics_bp.get("/teacher/class/<class_id>/heatmap")
@jwt_required()
@role_required("teacher")
def class_heatmap(class_id: str):
    school_class = _owned_class(class_id, str(get_jwt_identity()))
    if school_class is None:
        return jsonify({"error": {"code": "class_not_found", "message": "Class not found"}}), 404
    students = _student_progress(school_class.get("student_ids", []))
    concepts = list(mongo.db.curriculum.find({"review_status": "approved"}, {"concept_id": 1, "title": 1, "subject": 1}))
    columns = [{"concept_id": item["concept_id"], "title": item.get("title", {}).get("ta", ""), "subject": item.get("subject", "")} for item in concepts]
    rows = []
    for student in students:
        by_concept = {item["concept_id"]: item for item in student["mastery"]}
        rows.append({
            "student_id": student["id"],
            "name": student["name"],
            "mastery": {concept["concept_id"]: by_concept.get(concept["concept_id"], {}).get("M") for concept in concepts},
            "keyword_mastery": {concept["concept_id"]: by_concept.get(concept["concept_id"], {}).get("L") for concept in concepts},
            "stages": {concept["concept_id"]: by_concept.get(concept["concept_id"], {}).get("stage", 0) for concept in concepts},
        })
    return jsonify({"concepts": columns, "students": rows})


@analytics_bp.get("/teacher/student/<student_id>")
@jwt_required()
@role_required("teacher")
def student_detail(student_id: str):
    teacher_id = str(get_jwt_identity())
    try:
        object_id = ObjectId(student_id)
    except Exception:
        return jsonify({"error": {"code": "student_not_found", "message": "Student not found"}}), 404
    student = mongo.db.users.find_one({"_id": object_id, "role": "student"})
    if student is None or not student.get("class_id") or _owned_class(student["class_id"], teacher_id) is None:
        return jsonify({"error": {"code": "student_not_found", "message": "Student not found"}}), 404
    progress = list(mongo.db.mastery.find({"user_id": student_id}, {"_id": 0, "concept_id": 1, "M": 1, "L": 1, "stage": 1, "recent": 1}))
    events = list(mongo.db.events.find({"user_id": student_id}).sort("ts", -1).limit(30))
    for event in events:
        event["id"] = str(event.pop("_id"))
        event["ts"] = event.get("ts").isoformat() if event.get("ts") else None
    return jsonify({"student": {"id": student_id, "name": student["name"], "grade": student.get("grade")}, "mastery": progress, "events": events})


class AttendanceRequest(BaseModel):
    date: date
    entries: list[dict[str, object]] = Field(min_length=1)


@analytics_bp.route("/teacher/attendance", methods=["GET", "POST"])
@jwt_required()
@role_required("teacher")
def attendance():
    teacher_id = str(get_jwt_identity())
    if request.method == "GET":
        school_class = mongo.db.classes.find_one({"teacher_id": teacher_id})
        if school_class is None:
            return jsonify({"attendance": {}})
        day = request.args.get("date", date.today().isoformat())
        try:
            day = date.fromisoformat(day).isoformat()
        except ValueError:
            return jsonify({"error": {"code": "invalid_date", "message": "Date must use YYYY-MM-DD format"}}), 422
        records = mongo.db.attendance.find({"user_id": {"$in": school_class.get("student_ids", [])}, "date": day})
        return jsonify({"date": day, "attendance": {record["user_id"]: record["present"] for record in records}})
    try:
        payload = AttendanceRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return jsonify({"error": {"code": "validation_error", "message": "Invalid attendance payload", "fields": error.errors(include_input=False)}}), 422
    student_ids = [str(entry.get("user_id", "")) for entry in payload.entries]
    school_class = mongo.db.classes.find_one({"teacher_id": teacher_id, "student_ids": {"$all": student_ids}})
    if not school_class or any(not entry.get("user_id") or not isinstance(entry.get("present"), bool) for entry in payload.entries):
        return jsonify({"error": {"code": "invalid_attendance", "message": "Attendance must include students from your class"}}), 403
    for entry in payload.entries:
        mongo.db.attendance.update_one(
            {"user_id": str(entry["user_id"]), "date": payload.date.isoformat()},
            {"$set": {"present": entry["present"], "recorded_by": teacher_id, "updated_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
    return jsonify({"saved": len(payload.entries), "date": payload.date.isoformat()})


@analytics_bp.get("/parent/child/<student_id>")
@jwt_required()
@role_required("parent")
def child_progress(student_id: str):
    parent = current_user()
    if student_id not in parent.get("linked_students", []):
        return jsonify({"error": {"code": "child_not_found", "message": "Linked child not found"}}), 404
    try:
        object_id = ObjectId(student_id)
    except Exception:
        return jsonify({"error": {"code": "child_not_found", "message": "Linked child not found"}}), 404
    child = mongo.db.users.find_one({"_id": object_id, "role": "student"})
    if child is None:
        return jsonify({"error": {"code": "child_not_found", "message": "Linked child not found"}}), 404
    attendance_records = list(mongo.db.attendance.find({"user_id": student_id}).sort("date", -1).limit(60))
    mastery = list(mongo.db.mastery.find({"user_id": student_id}, {"concept_id": 1, "M": 1, "stage": 1}))
    localized_progress = []
    language = child.get("language", "ta")
    for item in mastery:
        concept = mongo.db.curriculum.find_one({"concept_id": item["concept_id"]}, {"title": 1, "subject": 1}) or {}
        localized_progress.append({
            "concept_id": item["concept_id"],
            "title": concept.get("title", {}).get(language) or concept.get("title", {}).get("ta", item["concept_id"]),
            "subject": concept.get("subject", ""),
            "M": item.get("M", 0),
            "stage": item.get("stage", 0),
        })
    return jsonify({
        "child": {"id": student_id, "name": child["name"], "grade": child.get("grade")},
        "attendance": [{"date": item["date"], "present": item["present"]} for item in attendance_records],
        "progress": localized_progress,
        "recent_activity": {
            "last_login": child.get("last_login").isoformat() if child.get("last_login") else None,
            "last_lesson": child.get("last_lesson_at").isoformat() if child.get("last_lesson_at") else None,
        },
        "stage_note": "Stage shows the amount of English support, not English proficiency.",
    })