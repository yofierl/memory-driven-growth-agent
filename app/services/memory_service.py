from __future__ import annotations

from datetime import UTC, datetime

from app.models.memory import Memory
from app.services.normalization import normalize_behavior, normalize_emotion, normalize_trigger


class MemoryService:
    def __init__(self, provider) -> None:
        self.provider = provider

    def add_memory(self, memory: Memory) -> Memory:
        candidate = self._find_merge_candidate(memory)
        if candidate is not None:
            return self.provider.update_memory(
                candidate.memory_id,
                {
                    "frequency": candidate.frequency + 1,
                    "last_seen_at": datetime.now(UTC),
                    "importance": max(candidate.importance, memory.importance),
                    "confidence": max(candidate.confidence, memory.confidence),
                },
            )
        return self.provider.add_memory(memory)

    def search_memories(
        self,
        query: str,
        filters: dict | None = None,
        top_k: int = 3,
    ) -> list[Memory]:
        return self.provider.search_memories(query=query, filters=filters, top_k=top_k)

    def list_memories(self, user_id: str, filters: dict | None = None) -> list[Memory]:
        return self.provider.list_memories(user_id=user_id, filters=filters)

    def update_memory(self, memory_id: str, patch: dict) -> Memory:
        return self.provider.update_memory(memory_id=memory_id, patch=patch)

    def delete_memory(self, memory_id: str) -> bool:
        return self.provider.delete_memory(memory_id=memory_id)

    def _find_merge_candidate(self, memory: Memory) -> Memory | None:
        existing_memories = self.provider.list_memories(
            user_id=memory.user_id,
            filters={"type": memory.type},
        )
        for existing in existing_memories:
            if self._same_event_chain(existing, memory):
                return existing
        return None

    @staticmethod
    def _same_event_chain(left: Memory, right: Memory) -> bool:
        required_fields = ("emotion", "trigger", "behavior")
        for field in required_fields:
            left_value = getattr(left, field)
            right_value = getattr(right, field)
            if not left_value or not right_value:
                return False
            if field == "emotion":
                left_value = normalize_emotion(str(left_value))
                right_value = normalize_emotion(str(right_value))
            elif field == "trigger":
                left_value = normalize_trigger(str(left_value))
                right_value = normalize_trigger(str(right_value))
            else:
                left_value = normalize_behavior(str(left_value))
                right_value = normalize_behavior(str(right_value))
            if left_value != right_value:
                return False
        return True
