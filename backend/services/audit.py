from datetime import datetime, timezone

from backend.extensions import mongo


def write_audit(actor_id: str, action: str, target: str, before=None, after=None) -> None:
    mongo.db.audit_log.insert_one({
        "actor_id": actor_id,
        "action": action,
        "target": target,
        "before": before,
        "after": after,
        "ts": datetime.now(timezone.utc),
    })