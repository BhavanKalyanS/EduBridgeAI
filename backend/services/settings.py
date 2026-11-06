from flask import current_app

from backend.extensions import mongo
from backend.services.bkt import BKTParameters
from backend.services.stage_controller import StageThresholds


def learning_settings() -> tuple[BKTParameters, StageThresholds]:
    stored = mongo.db.settings.find_one({"_id": "learning"}) or {}
    bkt = stored.get("bkt", {})
    thresholds = stored.get("thresholds", {})
    return (
        BKTParameters(
            initial_mastery=bkt.get("P0", current_app.config["BKT_P0"]),
            learning_rate=bkt.get("T", current_app.config["BKT_T"]),
            guess=bkt.get("g", current_app.config["BKT_G"]),
            slip=bkt.get("s", current_app.config["BKT_S"]),
        ),
        StageThresholds(
            promote_mastery=thresholds.get("promote_M", current_app.config["PROMOTE_M"]),
            promote_keywords=thresholds.get("promote_L", current_app.config["PROMOTE_L"]),
            regress_mastery=thresholds.get("regress_M", current_app.config["REGRESS_M"]),
            streak=int(thresholds.get("streak", current_app.config["STAGE_STREAK"])),
        ),
    )