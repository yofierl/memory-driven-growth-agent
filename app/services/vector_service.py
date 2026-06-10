from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from pymilvus import Collection, connections

from app.core.config import Settings, get_settings
from app.models.memory import Memory


@dataclass(frozen=True)
class VectorSearchResult:
    memory_id: str
    embedding_id: str | None
    score: float


def build_memory_text(memory: Memory) -> str:
    parts = [
        ("场景", memory.scenario),
        ("事件", memory.event),
        ("情绪", memory.emotion),
        ("触发因素", memory.trigger),
        ("行为", memory.behavior),
        ("结果", memory.result),
    ]
    return "\n".join(f"{label}：{value}" for label, value in parts if value)


class VectorService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.collection_name = self.settings.milvus_collection
        self.dimension = self.settings.embedding_dimension
        self._alias = "memory_vector_service"

    def upsert_embedding(self, memory: Memory) -> str:
        if memory.embedding_id is None:
            raise ValueError("memory.embedding_id is required before vector upsert")
        collection = self._collection()
        collection.upsert(
            [
                {
                    "embedding_id": memory.embedding_id,
                    "memory_id": memory.memory_id,
                    "user_id": memory.user_id,
                    "type": memory.type,
                    "scenario": memory.scenario or "",
                    "created_at": int(memory.created_at.timestamp()),
                    "embedding": self.embed_text(build_memory_text(memory)),
                }
            ]
        )
        collection.flush()
        return memory.embedding_id

    def search(
        self,
        query: str,
        user_id: str,
        top_k: int = 3,
        filters: dict | None = None,
    ) -> list[VectorSearchResult]:
        collection = self._collection()
        collection.load()
        expr_parts = [f'user_id == "{self._escape_expr(user_id)}"']
        memory_type = (filters or {}).get("type")
        if isinstance(memory_type, str):
            expr_parts.append(f'type == "{self._escape_expr(memory_type)}"')
        expr = " and ".join(expr_parts)
        results = collection.search(
            data=[self.embed_text(query)],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"ef": 64}},
            limit=top_k,
            expr=expr,
            output_fields=["memory_id", "embedding_id"],
        )
        hits = results[0] if results else []
        parsed: list[VectorSearchResult] = []
        for hit in hits:
            entity = hit.entity
            parsed.append(
                VectorSearchResult(
                    memory_id=entity.get("memory_id"),
                    embedding_id=entity.get("embedding_id"),
                    score=float(hit.score),
                )
            )
        return parsed

    def delete_embedding(self, embedding_id: str) -> None:
        collection = self._collection()
        collection.delete(f'embedding_id == "{self._escape_expr(embedding_id)}"')
        collection.flush()

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        normalized_text = "".join(text.lower().split())
        if not normalized_text:
            return vector
        tokens = self._tokens(normalized_text)
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def _collection(self) -> Collection:
        if not connections.has_connection(self._alias):
            connections.connect(
                alias=self._alias,
                host=self.settings.milvus_host,
                port=self.settings.milvus_port,
            )
        return Collection(name=self.collection_name, using=self._alias)

    @staticmethod
    def _tokens(text: str) -> list[str]:
        chars = list(text)
        bigrams = [text[index : index + 2] for index in range(max(len(text) - 1, 0))]
        trigrams = [text[index : index + 3] for index in range(max(len(text) - 2, 0))]
        return chars + bigrams + trigrams

    @staticmethod
    def _escape_expr(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')
