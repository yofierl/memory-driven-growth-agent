from __future__ import annotations

from datetime import UTC, datetime

from pymongo.collection import Collection

from app.models.user import User


class UserRepository:
    def __init__(self, collection: Collection) -> None:
        self.collection = collection

    def get_by_user_id(self, user_id: str) -> User | None:
        document = self.collection.find_one({"user_id": user_id})
        if document is None:
            return None
        document.pop("_id", None)
        return User.model_validate(document)

    def upsert(self, user: User) -> User:
        payload = user.model_dump(mode="python")
        payload["updated_at"] = datetime.now(UTC)
        self.collection.update_one(
            {"user_id": user.user_id},
            {
                "$set": {k: v for k, v in payload.items() if k != "created_at"},
                "$setOnInsert": {"created_at": payload["created_at"]},
            },
            upsert=True,
        )
        stored = self.get_by_user_id(user.user_id)
        return stored or user
