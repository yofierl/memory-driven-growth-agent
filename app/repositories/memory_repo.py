from __future__ import annotations

from pymongo.collection import Collection

from app.models.memory import Memory


class MemoryRepository:
    def __init__(self, collection: Collection) -> None:
        self.collection = collection

    def create_many(self, memories: list[Memory]) -> list[Memory]:
        if not memories:
            return []
        payloads = [memory.model_dump(mode="python") for memory in memories]
        self.collection.insert_many(payloads)
        return memories

    def list_by_user_id(self, user_id: str, memory_type: str | None = None) -> list[Memory]:
        query: dict[str, object] = {"user_id": user_id}
        if memory_type is not None:
            query["type"] = memory_type
        cursor = self.collection.find(query).sort("created_at", -1)
        results: list[Memory] = []
        for document in cursor:
            document.pop("_id", None)
            results.append(Memory.model_validate(document))
        return results
