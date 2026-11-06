from backend.app import app
from backend.extensions import mongo


def initialize_indexes() -> None:
    with app.app_context():
        mongo.db.users.create_index("email", unique=True)
        mongo.db.classes.create_index("class_id", unique=True)
        mongo.db.attendance.create_index([("user_id", 1), ("date", 1)], unique=True)
        mongo.db.curriculum.create_index("concept_id", unique=True)
        mongo.db.mastery.create_index([("user_id", 1), ("concept_id", 1)], unique=True)
        mongo.db.events.create_index("event_id", unique=True)
        mongo.db.events.create_index([("user_id", 1), ("ts", -1)])
        mongo.db.audit_log.create_index([("ts", -1)])


if __name__ == "__main__":
    initialize_indexes()