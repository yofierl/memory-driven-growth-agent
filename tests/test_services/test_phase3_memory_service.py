from app.models.memory import Memory
from app.services.memory_service import MemoryService


class FakeMemoryProvider:
    def __init__(self) -> None:
        self.memories: dict[str, Memory] = {}
        self.deleted_ids: set[str] = set()
        self.search_calls: list[dict[str, object]] = []

    def add_memory(self, memory: Memory) -> Memory:
        self.memories[memory.memory_id] = memory
        return memory

    def search_memories(
        self,
        query: str,
        filters: dict | None = None,
        top_k: int = 3,
    ) -> list[Memory]:
        self.search_calls.append({"query": query, "filters": filters, "top_k": top_k})
        active_memories = [
            memory
            for memory_id, memory in self.memories.items()
            if memory_id not in self.deleted_ids
        ]
        return active_memories[:top_k]

    def list_memories(self, user_id: str, filters: dict | None = None) -> list[Memory]:
        return [
            memory
            for memory_id, memory in self.memories.items()
            if memory.user_id == user_id and memory_id not in self.deleted_ids
        ]

    def update_memory(self, memory_id: str, patch: dict) -> Memory:
        current = self.memories[memory_id]
        updated = current.model_copy(update=patch)
        self.memories[memory_id] = updated
        return updated

    def delete_memory(self, memory_id: str) -> bool:
        self.deleted_ids.add(memory_id)
        return True


def make_memory(
    memory_id: str,
    event: str,
    behavior: str = "刷视频回避",
    trigger: str = "任务压力",
) -> Memory:
    return Memory(
        memory_id=memory_id,
        user_id="user-1",
        type="emotion_event",
        scenario="学习",
        event=event,
        emotion="焦虑",
        trigger=trigger,
        behavior=behavior,
        result="学习中断",
        confidence=0.9,
    )


def test_memory_service_exposes_stable_search_and_delete_interface() -> None:
    provider = FakeMemoryProvider()
    service = MemoryService(provider=provider)
    service.add_memory(make_memory("memory-1", "准备面试时学不进去"))
    service.add_memory(
        make_memory(
            "memory-2",
            "写简历时拖延",
            behavior="反复修改标题",
            trigger="简历措辞不确定",
        )
    )

    before_delete = service.search_memories(
        query="我又学不进去了",
        filters={"user_id": "user-1"},
        top_k=3,
    )
    service.delete_memory("memory-1")
    after_delete = service.search_memories(
        query="我又学不进去了",
        filters={"user_id": "user-1"},
        top_k=3,
    )

    assert [memory.memory_id for memory in before_delete] == ["memory-1", "memory-2"]
    assert [memory.memory_id for memory in after_delete] == ["memory-2"]
    assert provider.search_calls[0]["top_k"] == 3
