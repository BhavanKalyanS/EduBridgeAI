from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from backend.middleware.rbac import role_required

tutor_bp = Blueprint("tutor", __name__)


@tutor_bp.route("/tutor", methods=["GET", "POST"])
@jwt_required()
@role_required("student")
def tutor_stub():
    return jsonify({"error": {"code": "not_implemented", "message": "The tutor is not available in Phase 1"}}), 501


@tutor_bp.post("/events/sync")
@jwt_required()
@role_required("student")
def event_sync_stub():
    return jsonify({"error": {"code": "not_implemented", "message": "Offline event sync is not available in Phase 1"}}), 501