import bcrypt
from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from pydantic import ValidationError

from backend.extensions import mongo
from backend.middleware.rbac import role_required
from backend.schemas.requests import ClassRequest, CurriculumRequest, SettingsRequest, UserCreateRequest, UserUpdateRequest
from backend.services.audit import write_audit
from backend.services.authz import json_document, public_user

admin_bp = Blueprint("admin", __name__)


def _object_id(value: str):
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def _invalid(error: ValidationError, message: str):
    return jsonify({"error": {"code": "validation_error", "message": message, "fields": error.errors(include_input=False)}}), 422


def _validate_class_members(payload: ClassRequest):
    teacher_id = _object_id(payload.teacher_id)
    teacher = mongo.db.users.find_one({"_id": teacher_id, "role": "teacher", "active": True}) if teacher_id else None
    if teacher is None:
        return None, None, (jsonify({"error": {"code": "invalid_teacher", "message": "Select an active teacher"}}), 422)
    student_ids = list(dict.fromkeys(payload.student_ids))
    if len(student_ids) != len(payload.student_ids):
        return None, None, (jsonify({"error": {"code": "duplicate_student", "message": "A student can appear only once in a class"}}), 422)
    students = []
    for student_id in student_ids:
        object_id = _object_id(student_id)
        student = mongo.db.users.find_one({"_id": object_id, "role": "student", "active": True}) if object_id else None
        if student is None:
            return None, None, (jsonify({"error": {"code": "invalid_student", "message": "Every class member must be an active student"}}), 422)
        if student.get("class_id") not in (None, payload.class_id):
            return None, None, (jsonify({"error": {"code": "student_in_other_class", "message": "A student is already assigned to another class"}}), 409)
        students.append(student)
    return teacher, students, None


@admin_bp.get("/admin/overview")
@jwt_required()
@role_required("admin")
def overview():
    return jsonify({
        "users": mongo.db.users.count_documents({"active": True}),
        "classes": mongo.db.classes.count_documents({}),
        "concepts": mongo.db.curriculum.count_documents({}),
        "database": "connected",
    })


@admin_bp.get("/admin/users")
@jwt_required()
@role_required("admin")
def list_users():
    role = request.args.get("role")
    query = {"role": role} if role in {"student", "teacher", "parent", "admin"} else {}
    users = [public_user(user) | {"active": user.get("active", True)} for user in mongo.db.users.find(query).sort("name", 1).limit(500)]
    return jsonify({"users": users})


@admin_bp.post("/admin/users")
@jwt_required()
@role_required("admin")
def create_user():
    try:
        payload = UserCreateRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return _invalid(error, "Invalid user details")
    if mongo.db.users.find_one({"email": payload.email.lower()}):
        return jsonify({"error": {"code": "email_exists", "message": "An account with this email already exists"}}), 409
    linked_students = list(dict.fromkeys(payload.linked_students))
    if len(linked_students) != len(payload.linked_students):
        return jsonify({"error": {"code": "duplicate_student", "message": "A linked student can appear only once"}}), 422
    if linked_students and payload.role != "parent":
        return jsonify({"error": {"code": "invalid_parent_links", "message": "Only parent accounts can link students"}}), 422
    for student_id in linked_students:
        student_object_id = _object_id(student_id)
        if not student_object_id or not mongo.db.users.find_one({"_id": student_object_id, "role": "student", "active": True}):
            return jsonify({"error": {"code": "invalid_student", "message": "Every linked account must be an active student"}}), 422
    if payload.class_id:
        return jsonify({"error": {"code": "assign_roster", "message": "Assign students and teachers through class management"}}), 422
    user = payload.model_dump(exclude={"password", "class_id"})
    user["linked_students"] = linked_students
    user["email"] = payload.email.lower()
    user["password_hash"] = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    user["active"] = True
    inserted = mongo.db.users.insert_one(user)
    user["_id"] = inserted.inserted_id
    write_audit(str(get_jwt_identity()), "user.create", str(inserted.inserted_id), after={"role": user["role"], "email": user["email"]})
    return jsonify({"user": public_user(user)}), 201


@admin_bp.patch("/admin/users/<user_id>")
@jwt_required()
@role_required("admin")
def update_user(user_id: str):
    object_id = _object_id(user_id)
    if object_id is None:
        return jsonify({"error": {"code": "user_not_found", "message": "User not found"}}), 404
    try:
        payload = UserUpdateRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return _invalid(error, "Invalid user update")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return jsonify({"error": {"code": "empty_update", "message": "Provide at least one field to update"}}), 422
    password = changes.pop("password", None)
    if password:
        changes["password_hash"] = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    before = mongo.db.users.find_one({"_id": object_id})
    if before is None:
        return jsonify({"error": {"code": "user_not_found", "message": "User not found"}}), 404
    linked_students = changes.get("linked_students")
    target_role = changes.get("role", before.get("role"))
    if linked_students is not None:
        if target_role != "parent" and linked_students:
            return jsonify({"error": {"code": "invalid_parent_links", "message": "Only parent accounts can link students"}}), 422
        if len(set(linked_students)) != len(linked_students):
            return jsonify({"error": {"code": "duplicate_student", "message": "A linked student can appear only once"}}), 422
        for student_id in linked_students:
            student_object_id = _object_id(student_id)
            if not student_object_id or not mongo.db.users.find_one({"_id": student_object_id, "role": "student", "active": True}):
                return jsonify({"error": {"code": "invalid_student", "message": "Every linked account must be an active student"}}), 422
    class_id = changes.get("class_id")
    if class_id:
        if target_role != "student" or not mongo.db.classes.find_one({"class_id": class_id, "student_ids": str(object_id)}):
            return jsonify({"error": {"code": "invalid_class_assignment", "message": "Assign students through class management"}}), 422
    elif class_id == "":
        changes.pop("class_id")
    mongo.db.users.update_one({"_id": object_id}, {"$set": changes})
    after = mongo.db.users.find_one({"_id": object_id})
    write_audit(str(get_jwt_identity()), "user.update", user_id, before={"role": before.get("role"), "active": before.get("active"), "consent": before.get("consent")}, after={"role": after.get("role"), "active": after.get("active"), "consent": after.get("consent")})
    return jsonify({"user": public_user(after) | {"active": after.get("active", True)}})


@admin_bp.delete("/admin/users/<user_id>")
@jwt_required()
@role_required("admin")
def deactivate_user(user_id: str):
    object_id = _object_id(user_id)
    if object_id is None or not mongo.db.users.find_one({"_id": object_id}):
        return jsonify({"error": {"code": "user_not_found", "message": "User not found"}}), 404
    if user_id == str(get_jwt_identity()):
        return jsonify({"error": {"code": "self_deactivation", "message": "You cannot deactivate your own account"}}), 409
    mongo.db.users.update_one({"_id": object_id}, {"$set": {"active": False}})
    write_audit(str(get_jwt_identity()), "user.deactivate", user_id)
    return "", 204


@admin_bp.route("/admin/classes", methods=["GET", "POST"])
@jwt_required()
@role_required("admin")
def classes():
    if request.method == "GET":
        result = [json_document(item) for item in mongo.db.classes.find().sort("name", 1)]
        return jsonify({"classes": result})
    try:
        payload = ClassRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return _invalid(error, "Invalid class details")
    if mongo.db.classes.find_one({"class_id": payload.class_id}):
        return jsonify({"error": {"code": "class_exists", "message": "Class ID already exists"}}), 409
    teacher, students, error_response = _validate_class_members(payload)
    if error_response:
        return error_response
    record = payload.model_dump()
    record["student_ids"] = list(dict.fromkeys(record["student_ids"]))
    inserted = mongo.db.classes.insert_one(record)
    mongo.db.users.update_one({"_id": teacher["_id"]}, {"$set": {"class_id": payload.class_id}})
    for student in students:
        mongo.db.users.update_one({"_id": student["_id"]}, {"$set": {"class_id": payload.class_id}})
    write_audit(str(get_jwt_identity()), "class.create", payload.class_id, after={"name": payload.name})
    return jsonify({"class": {"id": str(inserted.inserted_id), **record}}), 201


@admin_bp.route("/admin/classes/<class_id>", methods=["PUT", "DELETE"])
@jwt_required()
@role_required("admin")
def class_item(class_id: str):
    before = mongo.db.classes.find_one({"class_id": class_id})
    if before is None:
        return jsonify({"error": {"code": "class_not_found", "message": "Class not found"}}), 404
    if request.method == "DELETE":
        mongo.db.classes.delete_one({"_id": before["_id"]})
        mongo.db.users.update_many({"_id": _object_id(before["teacher_id"])}, {"$unset": {"class_id": ""}})
        mongo.db.users.update_many({"_id": {"$in": [_object_id(value) for value in before.get("student_ids", [])]}}, {"$unset": {"class_id": ""}})
        write_audit(str(get_jwt_identity()), "class.delete", class_id, before={"name": before.get("name")})
        return "", 204
    try:
        payload = ClassRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return _invalid(error, "Invalid class details")
    if payload.class_id != class_id:
        return jsonify({"error": {"code": "immutable_class_id", "message": "Class ID cannot be changed"}}), 422
    teacher, students, error_response = _validate_class_members(payload)
    if error_response:
        return error_response
    previous_student_ids = set(before.get("student_ids", []))
    next_student_ids = set(payload.student_ids)
    removed_ids = [_object_id(value) for value in previous_student_ids - next_student_ids]
    if removed_ids:
        mongo.db.users.update_many({"_id": {"$in": removed_ids}}, {"$unset": {"class_id": ""}})
    mongo.db.classes.update_one({"_id": before["_id"]}, {"$set": payload.model_dump()})
    mongo.db.users.update_one({"_id": teacher["_id"]}, {"$set": {"class_id": class_id}})
    for student in students:
        mongo.db.users.update_one({"_id": student["_id"]}, {"$set": {"class_id": class_id}})
    write_audit(str(get_jwt_identity()), "class.update", class_id, before={"name": before.get("name")}, after={"name": payload.name})
    return jsonify({"class": payload.model_dump()})


@admin_bp.route("/admin/curriculum", methods=["GET", "POST"])
@jwt_required()
@role_required("admin")
def curriculum():
    if request.method == "GET":
        result = [json_document(item) for item in mongo.db.curriculum.find().sort([("subject", 1), ("chapter", 1)])]
        return jsonify({"concepts": result})
    try:
        payload = CurriculumRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return _invalid(error, "Invalid curriculum content")
    if mongo.db.curriculum.find_one({"concept_id": payload.concept_id}):
        return jsonify({"error": {"code": "concept_exists", "message": "Concept ID already exists"}}), 409
    record = payload.model_dump()
    inserted = mongo.db.curriculum.insert_one(record)
    write_audit(str(get_jwt_identity()), "curriculum.create", payload.concept_id, after={"review_status": payload.review_status})
    return jsonify({"concept": {"id": str(inserted.inserted_id), **record}}), 201


@admin_bp.route("/admin/curriculum/<concept_id>", methods=["PUT", "DELETE"])
@jwt_required()
@role_required("admin")
def curriculum_item(concept_id: str):
    before = mongo.db.curriculum.find_one({"concept_id": concept_id})
    if before is None:
        return jsonify({"error": {"code": "concept_not_found", "message": "Concept not found"}}), 404
    if request.method == "DELETE":
        mongo.db.curriculum.delete_one({"_id": before["_id"]})
        write_audit(str(get_jwt_identity()), "curriculum.delete", concept_id, before={"review_status": before.get("review_status")})
        return "", 204
    try:
        payload = CurriculumRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return _invalid(error, "Invalid curriculum content")
    if payload.concept_id != concept_id:
        return jsonify({"error": {"code": "immutable_concept_id", "message": "Concept ID cannot be changed"}}), 422
    mongo.db.curriculum.update_one({"_id": before["_id"]}, {"$set": payload.model_dump()})
    write_audit(str(get_jwt_identity()), "curriculum.update", concept_id, before={"review_status": before.get("review_status")}, after={"review_status": payload.review_status})
    return jsonify({"concept": payload.model_dump()})


@admin_bp.route("/admin/settings", methods=["GET", "PUT"])
@jwt_required()
@role_required("admin")
def settings():
    if request.method == "GET":
        stored = mongo.db.settings.find_one({"_id": "learning"})
        if stored:
            stored.pop("_id", None)
            return jsonify({"settings": stored, "tuned": False})
        from backend.services.settings import learning_settings

        bkt, thresholds = learning_settings()
        return jsonify({"settings": {"bkt": {"P0": bkt.initial_mastery, "T": bkt.learning_rate, "g": bkt.guess, "s": bkt.slip}, "thresholds": {"promote_M": thresholds.promote_mastery, "promote_L": thresholds.promote_keywords, "regress_M": thresholds.regress_mastery, "streak": thresholds.streak}}, "tuned": False})
    try:
        payload = SettingsRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return _invalid(error, "Invalid learning settings")
    settings_data = payload.model_dump()
    if set(settings_data["bkt"]) != {"P0", "T", "g", "s"} or set(settings_data["thresholds"]) != {"promote_M", "promote_L", "regress_M", "streak"}:
        return jsonify({"error": {"code": "invalid_settings", "message": "Provide all supported BKT parameters and thresholds"}}), 422
    if any(not 0 <= value <= 1 for value in settings_data["bkt"].values()) or any(not 0 <= value <= 1 for key, value in settings_data["thresholds"].items() if key != "streak") or int(settings_data["thresholds"]["streak"]) < 1:
        return jsonify({"error": {"code": "invalid_settings", "message": "Probabilities must be between 0 and 1 and streak must be positive"}}), 422
    before = mongo.db.settings.find_one({"_id": "learning"})
    mongo.db.settings.update_one({"_id": "learning"}, {"$set": settings_data}, upsert=True)
    write_audit(str(get_jwt_identity()), "settings.update", "learning", before=before, after=settings_data)
    return jsonify({"settings": settings_data, "tuned": False})


@admin_bp.get("/admin/events")
@jwt_required()
@role_required("admin")
def events():
    page = max(1, request.args.get("page", default=1, type=int))
    limit = min(100, max(1, request.args.get("limit", default=50, type=int)))
    query = {}
    valid = request.args.get("valid")
    if valid in {"true", "false"}:
        query["valid"] = valid == "true"
    items = list(mongo.db.events.find(query).sort("ts", -1).skip((page - 1) * limit).limit(limit))
    for item in items:
        item["id"] = str(item.pop("_id"))
        if item.get("ts"):
            item["ts"] = item["ts"].isoformat()
    return jsonify({"events": items, "page": page, "limit": limit, "total": mongo.db.events.count_documents(query)})


@admin_bp.get("/admin/audit")
@jwt_required()
@role_required("admin")
def audit_log():
    items = list(mongo.db.audit_log.find().sort("ts", -1).limit(100))
    for item in items:
        item["id"] = str(item.pop("_id"))
        item["ts"] = item["ts"].isoformat() if item.get("ts") else None
    return jsonify({"entries": items})


@admin_bp.get("/auth/data-export")
@jwt_required()
def data_export():
    user = mongo.db.users.find_one({"_id": _object_id(str(get_jwt_identity())), "active": True})
    if user is None:
        return jsonify({"error": {"code": "unauthorized", "message": "This account is unavailable"}}), 401
    identity = str(user["_id"])
    def export_collection(collection: str) -> list[dict]:
        records = list(getattr(mongo.db, collection).find({"user_id": identity}))
        return [json_document(record) for record in records]
    return jsonify({"user": public_user(user), "mastery": export_collection("mastery"), "events": export_collection("events"), "attendance": export_collection("attendance")})


@admin_bp.post("/auth/delete-request")
@jwt_required()
def delete_request():
    user = mongo.db.users.find_one({"_id": _object_id(str(get_jwt_identity())), "active": True})
    if user is None:
        return jsonify({"error": {"code": "unauthorized", "message": "This account is unavailable"}}), 401
    user_id = str(user["_id"])
    mongo.db.privacy_requests.insert_one({"user_id": user_id, "status": "pending", "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc)})
    return jsonify({"status": "pending", "message": "Your request was recorded for administrator review"}), 202


@admin_bp.get("/admin/privacy-requests")
@jwt_required()
@role_required("admin")
def privacy_requests():
    entries = [json_document(item) for item in mongo.db.privacy_requests.find().sort("created_at", -1).limit(100)]
    return jsonify({"requests": entries})