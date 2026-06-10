from __future__ import annotations

from datetime import UTC, datetime

from pymongo.collection import Collection

from app.core.exceptions import PatternNotFoundError
from app.models.pattern import Pattern


class PatternRepository:
    def __init__(self, collection: Collection) -> None:
        self.collection = collection

    def list_by_user_id(self, user_id: str, statuses: list[str] | None = None) -> list[Pattern]:
        query: dict[str, object] = {"user_id": user_id}
        if statuses:
            query["status"] = {"$in": statuses}
        cursor = self.collection.find(query).sort("created_at", -1)
        return [self._to_model(document) for document in cursor]

    def get_by_pattern_id(self, pattern_id: str) -> Pattern | None:
        document = self.collection.find_one({"pattern_id": pattern_id})
        return self._to_model(document) if document else None

    def get_detected_by_signature(
        self,
        *,
        user_id: str,
        scenario: str | None,
        trigger: str,
        emotion: str,
        behavior: str,
    ) -> Pattern | None:
        query: dict[str, object] = {
            "user_id": user_id,
            "trigger": trigger,
            "emotion": emotion,
            "behavior": behavior,
            "status": {"$ne": "rejected"},
        }
        if scenario is None:
            query["scenario"] = None
        else:
            query["scenario"] = scenario
        document = self.collection.find_one(query)
        return self._to_model(document) if document else None

    def upsert(self, pattern: Pattern) -> Pattern:
        payload = pattern.model_dump(mode="python")
        payload["updated_at"] = datetime.now(UTC)
        self.collection.update_one(
            {"pattern_id": pattern.pattern_id},
            {
                "$set": {k: v for k, v in payload.items() if k != "created_at"},
                "$setOnInsert": {"created_at": payload["created_at"]},
            },
            upsert=True,
        )
        stored = self.get_by_pattern_id(pattern.pattern_id)
        return stored or pattern

    def update_status(self, pattern_id: str, status: str) -> Pattern:
        result = self.collection.find_one_and_update(
            {"pattern_id": pattern_id},
            {"$set": {"status": status, "updated_at": datetime.now(UTC)}},
            return_document=True,
        )
        if result is None:
            raise PatternNotFoundError(f"Pattern not found: {pattern_id}")
        return self._to_model(result)

    @staticmethod
    def _to_model(document: dict | None) -> Pattern:
        assert document is not None
        document.pop("_id", None)
        return Pattern.model_validate(document)
