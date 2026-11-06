import bcrypt
from datetime import datetime, timezone

from backend.app import app
from backend.extensions import mongo

DEMO_PASSWORD = "EduBridgeDemo!2026"

USERS = [
    {"name": "Asha Student", "email": "student@example.com", "role": "student", "language": "ta", "board": "CBSE", "grade": "10", "class_id": "10A", "consent": True},
    {"name": "Kavin Student", "email": "student2@example.com", "role": "student", "language": "ta", "board": "CBSE", "grade": "10", "class_id": "10A", "consent": True},
    {"name": "Meera Student", "email": "student3@example.com", "role": "student", "language": "en", "board": "CBSE", "grade": "10", "class_id": "10A", "consent": True},
    {"name": "Arun Teacher", "email": "teacher@example.com", "role": "teacher", "language": "en", "class_id": "10A", "consent": False},
    {"name": "Asha Family", "email": "parent@example.com", "role": "parent", "language": "ta", "linked_email": "student@example.com", "consent": False},
    {"name": "Local Administrator", "email": "admin@example.com", "role": "admin", "language": "en", "consent": False},
]


def seed_users() -> None:
    with app.app_context():
        password_hash = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt()).decode()
        ids = {}
        for item in USERS:
            document = {key: value for key, value in item.items() if key != "linked_email"}
            document["password_hash"] = password_hash
            document["active"] = True
            document["linked_students"] = []
            mongo.db.users.update_one({"email": item["email"]}, {"$set": document}, upsert=True)
            ids[item["email"]] = mongo.db.users.find_one({"email": item["email"]})["_id"]
        parent = next(item for item in USERS if item["role"] == "parent")
        mongo.db.users.update_one({"_id": ids[parent["email"]]}, {"$set": {"linked_students": [str(ids[parent["linked_email"]])]}})
        student_ids = [str(ids[item["email"]]) for item in USERS if item["role"] == "student"]
        mongo.db.classes.delete_one({"class_id": "9A"})
        mongo.db.classes.update_one(
            {"class_id": "10A"},
            {"$set": {"name": "CBSE Class 10 · Section A", "teacher_id": str(ids["teacher@example.com"]), "student_ids": student_ids}},
            upsert=True,
        )
        mongo.db.users.update_many({"role": "student", "email": {"$in": [item["email"] for item in USERS if item["role"] == "student"]}}, {"$set": {"class_id": "10A", "grade": "10", "board": "CBSE"}})

        sample_levels = [0.32, 0.53, 0.71, 0.87]
        concept_ids = [item["concept_id"] for item in mongo.db.curriculum.find({"grade": "10", "board": "CBSE", "review_status": "approved"}, {"concept_id": 1}).sort("concept_id", 1)]
        mongo.db.mastery.delete_many({"user_id": {"$in": student_ids}, "concept_id": {"$nin": concept_ids}})
        for student_index, student_id in enumerate(student_ids):
            for concept_index, concept_id in enumerate(concept_ids):
                level = sample_levels[(student_index + concept_index) % len(sample_levels)]
                stage = min(4, max(0, round(level * 4)))
                mongo.db.mastery.update_one(
                    {"user_id": student_id, "concept_id": concept_id},
                        {"$setOnInsert": {"M": level, "L": max(0.2, level - 0.12), "stage": stage, "recent": [1, 1, 1], "updated_at": datetime.now(timezone.utc)}},
                    upsert=True,
                )
        print("Seeded synthetic demo accounts. Password for all accounts: " + DEMO_PASSWORD)


if __name__ == "__main__":
    seed_users()