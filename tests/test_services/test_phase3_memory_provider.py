from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from app.models.memory import Memory
from app.services.memory_provider import MongoMilvusMemoryProvider
from app.services.vector_service import VectorSearchResult


class FakeCursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self.documents = documents

    def sort(self, field: str, direction: int):
        reverse = direction < 0
        self.documents.sort(key=lambda item: item.get(field), reverse=reverse)
        return self

    def limit(self, count: int):
        self.documents = self.documents[:count]
        return self

    def __iter__(self):
        return iter(self.documents)


class FakeCollection:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def insert_one(self, document: dict[str, Any]) -> None:
        self.documents.append(deepcopy(document))

    def find(self, query: dict[str, Any]) -> FakeCursor:
        return FakeCursor([deepcopy(doc) for doc in self.documents if self._matches(doc, query)])

    def find_one(self, query: dict[str, Any]):
        for document in self.documents:
            if self._matches(document, query):
                return deepcopy(document)
        return None

    def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> None:
        for document in self.documents:
            if self._matches(document, query):
                document.update(update.get("$set", {}))
                return

    def _matches(self, document: dict[str, Any], query: dict[str, Any]) -> bool:
        for key, expected in query.items():
            if key == "$or":
                if not any(self._matches(document, item) for item in expected):
                    return False
                continue
            actual = document.get(key)
            if isinstance(expected, dict):
                if "$ne" in expected and actual == expected["$ne"]:
                    return False
                if "$in" in expected and actual not in expected["$in"]:
                    return False
                if "$regex" in expected:
                    pattern = expected["$regex"]
                    flags = re.IGNORECASE if expected.get("$options") == "i" else 0
                    if actual is None or re.search(pattern, str(actual), flags) is None:
                        return False
                continue
            if actual != expected:
                return False
        return True


class FakeVectorService:
    def __init__(self) -> None:
        self.upserted: list[Memory] = []
        self.deleted_embedding_ids: list[str] = []

    def upsert_embedding(self, memory: Memory) -> str:
        self.upserted.append(memory)
        return memory.embedding_id or ""

    def search(self, query: str, user_id: str, top_k: int = 3, filters: dict | None = None):
        return [
            VectorSearchResult(
                memory_id="memory-deleted",
                embedding_id="embedding-deleted",
                score=0.98,
            ),
            VectorSearchResult(
                memory_id="memory-active",
                embedding_id="embedding-active",
                score=0.91,
            ),
        ]

    def delete_embedding(self, embedding_id: str) -> None:
        self.deleted_embedding_ids.append(embedding_id)


def make_memory(memory_id: str, embedding_id: str) -> Memory:
    return Memory(
        memory_id=memory_id,
        user_id="user-1",
        type="emotion_event",
        event="准备面试时学不进去",
        emotion="焦虑",
        trigger="任务压力",
        behavior="刷视频回避",
        result="学习中断",
        confidence=0.9,
        embedding_id=embedding_id,
    )


def test_mongo_milvus_provider_filters_deleted_memories_from_vector_results() -> None:
    collection = FakeCollection()
    vector_service = FakeVectorService()
    provider = MongoMilvusMemoryProvider(collection, vector_service)
    provider.add_memory(make_memory("memory-deleted", "embedding-deleted"))
    provider.add_memory(make_memory("memory-active", "embedding-active"))
    provider.delete_memory("memory-deleted")

    results = provider.search_memories(
        query="我又学不进去了",
        filters={"user_id": "user-1", "type": "emotion_event"},
        top_k=3,
    )

    assert [memory.memory_id for memory in results] == ["memory-active"]
    assert vector_service.deleted_embedding_ids == ["embedding-deleted"]


def test_mongo_milvus_provider_deletes_old_embedding_before_update_upsert() -> None:
    collection = FakeCollection()
    vector_service = FakeVectorService()
    provider = MongoMilvusMemoryProvider(collection, vector_service)
    provider.add_memory(make_memory("memory-active", "embedding-active"))

    provider.update_memory("memory-active", {"behavior": "开始最小任务"})

    assert vector_service.deleted_embedding_ids == ["embedding-active"]
    assert vector_service.upserted[-1].memory_id == "memory-active"
