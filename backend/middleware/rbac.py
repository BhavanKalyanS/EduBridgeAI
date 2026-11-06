from functools import wraps
from typing import Callable

from flask import jsonify
from bson import ObjectId
from bson.errors import InvalidId
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from backend.extensions import mongo


def role_required(*allowed_roles: str) -> Callable:
    def decorate(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args, **kwargs):
            verify_jwt_in_request()
            try:
                user = mongo.db.users.find_one({"_id": ObjectId(get_jwt_identity()), "active": True})
            except (InvalidId, TypeError):
                user = None
            if user is None:
                return jsonify({"error": {"code": "unauthorized", "message": "This account is unavailable"}}), 401
            if user.get("role") not in allowed_roles or get_jwt().get("role") != user.get("role"):
                return jsonify({"error": {"code": "forbidden", "message": "You do not have permission to access this resource"}}), 403
            return view(*args, **kwargs)

        return wrapped

    return decorate