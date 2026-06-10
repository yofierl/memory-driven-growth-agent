from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from pymongo.collection import Collection

from app.models.memory import Memory
from app.services.vector_service import VectorService


class MongoMilvusMemoryProvider:
    def __init__(self, memory_collection: Collection, vector_service: VectorService) -> None:
        self.memory_collection = memory_collection
        self.vector_service = vector_service

    def add_memory(self, memory: Memory) -> Memory:
        memory_to_store = memory.model_copy(
            update={
                "embedding_id": memory.embedding_id or str(uuid4()),
                "updated_at": datetime.now(UTC),
            }
        )
        self.memory_collection.insert_one(memory_to_store.model_dump(mode="python"))
        self.vector_service.upsert_embedding(memory_to_store)
        return memory_to_store

    def search_memories(
        self,
        query: str,
        filters: dict | None = None,
        top_k: int = 3,
    ) -> list[Memory]:
        filters = filters or {}
        user_id = filters.get("user_id")
        if not isinstance(user_id, str) or not user_id:
            return []

        vector_results = self.vector_service.search(
            query=query,
            user_id=user_id,
            top_k=top_k * 2,
            filters=filters,
        )
        vector_ids = [result.memory_id for result in vector_results]
        vector_memories = self._find_active_by_ids(user_id=user_id, memory_ids=vector_ids)
        structured_memories = self._structured_search(
            user_id=user_id,
            query=query,
            filters=filters,
            limit=top_k,
        )
        return self._merge_and_dedupe(vector_memories + structured_memories, top_k=top_k)

    def list_memories(self, user_id: str, filters: dict | None = None) -> list[Memory]:
        query: dict[str, object] = {"user_id": user_id, "is_deleted": {"$ne": True}}
        for key, value in (filters or {}).items():
            if key == "user_id" or value is None:
                continue
            query[key] = value
        return [self._document_to_memory(doc) for doc in self.memory_collection.find(query)]

    def update_memory(self, memory_id: str, patch: dict) -> Memory:
        patch = {key: value for key, value in patch.items() if value is not None}
        patch["updated_at"] = datetime.now(UTC)
        self.memory_collection.update_one(
            {"memory_id": memory_id, "is_deleted": {"$ne": True}},
            {"$set": patch},
        )
        document = self.memory_collection.find_one(
            {"memory_id": memory_id, "is_deleted": {"$ne": True}}
        )
        if document is None:
            raise KeyError(memory_id)
        memory = self._document_to_memory(document)
        if memory.embedding_id:
            self.vector_service.upsert_embedding(memory)
        return memory

    def delete_memory(self, memory_id: str) -> bool:
        document = self.memory_collection.find_one(
            {"memory_id": memory_id, "is_deleted": {"$ne": True}}
        )
        if document is None:
            return False
        memory = self._document_to_memory(document)
        self.memory_collection.update_one(
            {"memory_id": memory_id},
            {
                "$set": {
                    "is_deleted": True,
                    "deleted_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
            },
        )
        if memory.embedding_id:
            self.vector_service.delete_embedding(memory.embedding_id)
        return True

    def _find_active_by_ids(self, user_id: str, memory_ids: list[str]) -> list[Memory]:
        if not memory_ids:
            return []
        docs = self.memory_collection.find(
            {
                "user_id": user_id,
                "memory_id": {"$in": memory_ids},
                "is_deleted": {"$ne": True},
            }
        )
        by_id = {doc["memory_id"]: self._document_to_memory(doc) for doc in docs}
        return [by_id[memory_id] for memory_id in memory_ids if memory_id in by_id]

    def _structured_search(
        self,
        user_id: str,
        query: str,
        filters: dict,
        limit: int,
    ) -> list[Memory]:
        mongo_query: dict[str, object] = {"user_id": user_id, "is_deleted": {"$ne": True}}
        memory_type = filters.get("type")
        if isinstance(memory_type, str):
            mongo_query["type"] = memory_type

        tokens = self._query_tokens(query)
        if tokens:
            mongo_query["$or"] = [
                {field: {"$regex": token, "$options": "i"}}
                for token in tokens
                for field in ("scenario", "event", "emotion", "trigger", "behavior", "result")
            ]

        cursor = self.memory_collection.find(mongo_query).sort("created_at", -1).limit(limit)
        return [self._document_to_memory(doc) for doc in cursor]

    @staticmethod
    def _merge_and_dedupe(memories: list[Memory], top_k: int) -> list[Memory]:
        deduped: list[Memory] = []
        seen: set[str] = set()
        for memory in memories:
            if memory.memory_id in seen or memory.is_deleted:
                continue
            seen.add(memory.memory_id)
            deduped.append(memory)
            if len(deduped) >= top_k:
                break
        return deduped

    @staticmethod
    def _document_to_memory(document: dict) -> Memory:
        document = dict(document)
        document.pop("_id", None)
        return Memory.model_validate(document)

    @staticmethod
    def _query_tokens(query: str) -> list[str]:
        cleaned = "".join(query.split())
        if not cleaned:
            return []
        escaped = re.escape(cleaned)
        important_bigrams = [
            re.escape(cleaned[index : index + 2]) for index in range(len(cleaned) - 1)
        ]
        return [escaped, *important_bigrams[:8]]
