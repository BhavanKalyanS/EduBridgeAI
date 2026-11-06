from bson import ObjectId
from bson.errors import InvalidId
from flask_jwt_extended import get_jwt_identity

from backend.extensions import mongo


def current_user():
    identity = get_jwt_identity()
    try:
        return mongo.db.users.find_one({"_id": ObjectId(identity), "active": True})
    except (InvalidId, TypeError):
        return None


def public_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "language": user.get("language", "ta"),
        "board": user.get("board", "CBSE"),
        "grade": user.get("grade"),
        "class_id": user.get("class_id"),
        "linked_students": user.get("linked_students", []),
        "consent": bool(user.get("consent", False)),
    }


def json_document(document: dict) -> dict:
    result = dict(document)
    if "_id" in result:
        result["id"] = str(result.pop("_id"))
    return result