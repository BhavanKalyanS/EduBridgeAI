import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _float_env(name: str, default: float) -> float:
    value = float(os.getenv(name, str(default)))
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1")
    return value


class Config:
    APP_ENV = os.getenv("APP_ENV", "development")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "local-only-change-me-to-a-long-random-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "local-only-change-this-jwt-key-to-a-long-random-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv("JWT_EXPIRES_MINUTES", "30")))
    JWT_TOKEN_LOCATION = ["headers"]
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/edubridge")
    MONGO_CONNECT_TIMEOUT_MS = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "3000"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    BKT_P0 = _float_env("BKT_P0", 0.30)
    BKT_T = _float_env("BKT_T", 0.10)
    BKT_G = _float_env("BKT_G", 0.20)
    BKT_S = _float_env("BKT_S", 0.10)
    PROMOTE_M = _float_env("PROMOTE_M", 0.85)
    PROMOTE_L = _float_env("PROMOTE_L", 0.70)
    REGRESS_M = _float_env("REGRESS_M", 0.40)
    STAGE_STREAK = int(os.getenv("STAGE_STREAK", "3"))
    LOGIN_RATE_LIMIT = os.getenv("LOGIN_RATE_LIMIT", "10 per minute")


class TestConfig(Config):
    APP_ENV = "testing"
    TESTING = True
    JWT_SECRET_KEY = "test-secret-key-with-at-least-thirty-two-bytes"