import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo.errors import PyMongoError

from backend.config import Config
from backend.extensions import jwt, limiter, mongo


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)
    mongo_uri = app.config.get("MONGO_URI", "")
    if mongo_uri and app.config["APP_ENV"] != "testing" and not mongo_uri.startswith("mongodb+srv://"):
        raise RuntimeError("Runtime database must be MongoDB Atlas using a mongodb+srv:// URI")
    if app.config["APP_ENV"] == "production" and (
        app.config["SECRET_KEY"] == "local-only-change-me-to-a-long-random-secret"
        or app.config["JWT_SECRET_KEY"] == "local-only-change-this-jwt-key-to-a-long-random-secret"
    ):
        raise RuntimeError("Production requires FLASK_SECRET_KEY and JWT_SECRET_KEY")
    jwt.init_app(app)
    limiter.init_app(app)
    if mongo_uri:
        mongo.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "http://localhost:5173")}})

    from backend.blueprints.admin import admin_bp
    from backend.blueprints.analytics import analytics_bp
    from backend.blueprints.auth import auth_bp
    from backend.blueprints.curriculum import curriculum_bp
    from backend.blueprints.learning import learning_bp
    from backend.blueprints.tutor import tutor_bp

    for blueprint in (auth_bp, curriculum_bp, learning_bp, analytics_bp, admin_bp, tutor_bp):
        app.register_blueprint(blueprint, url_prefix="/api")

    @app.before_request
    def require_database_configuration():
        if request.endpoint != "health" and not app.config.get("MONGO_URI"):
            return jsonify({"error": {"code": "database_not_configured", "message": "Configure MongoDB Atlas in MONGO_URI"}}), 503
        return None

    @app.get("/api/health")
    def health():
        if not app.config.get("MONGO_URI"):
            return jsonify({"status": "degraded", "database": "not_configured"}), 503
        try:
            mongo.cx.admin.command("ping")
            return jsonify({"status": "ok", "database": "connected"})
        except PyMongoError:
            return jsonify({"status": "degraded", "database": "unavailable"}), 503

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": {"code": "not_found", "message": "Resource not found"}}), 404

    @app.errorhandler(500)
    def internal_error(_error):
        return jsonify({"error": {"code": "internal_error", "message": "An unexpected error occurred"}}), 500

    @app.errorhandler(429)
    def too_many_requests(_error):
        return jsonify({"error": {"code": "rate_limited", "message": "Too many requests. Try again shortly."}}), 429

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))