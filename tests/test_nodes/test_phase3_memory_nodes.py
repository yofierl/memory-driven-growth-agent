from app.agent.nodes.memory_retrieval import MemoryRetrievalNode
from app.agent.nodes.memory_update import MemoryUpdateNode
from app.agent.state import GrowthAgentState
from app.models.memory import Memory


class FakeMemoryService:
    def __init__(self) -> None:
        self.search_calls: list[dict[str, object]] = []
        self.added_memories: list[Memory] = []

    def search_memories(self, query: str, filters: dict | None = None, top_k: int = 3):
        self.search_calls.append({"query": query, "filters": filters, "top_k": top_k})
        return [
            Memory(
                memory_id="memory-1",
                user_id="user-1",
                type="emotion_event",
                scenario="学习",
                event="准备面试时学不进去",
                emotion="焦虑",
                trigger="任务压力",
                behavior="刷视频回避",
                result="学习中断并自责",
                confidence=0.9,
            )
        ]

    def add_memory(self, memory: Memory) -> Memory:
        self.added_memories.append(memory)
        return memory


class FakeTaskService:
    def list_active_tasks(self, user_id: str):
        return [
            {
                "task_id": "task-1",
                "user_id": user_id,
                "task_content": "Start for 15 minutes",
                "status": "pending",
            }
        ]


def test_memory_retrieval_node_loads_top3_memories_through_memory_service() -> None:
    memory_service = FakeMemoryService()
    node = MemoryRetrievalNode(memory_service=memory_service)
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="我又学不进去了",
    )

    result = node.run(state)

    assert memory_service.search_calls == [
        {
            "query": "我又学不进去了",
            "filters": {"user_id": "user-1"},
            "top_k": 3,
        }
    ]
    assert result.retrieved_memories[0]["memory_id"] == "memory-1"
    assert result.retrieved_memories[0]["behavior"] == "刷视频回避"


def test_memory_retrieval_node_loads_active_tasks_when_task_service_exists() -> None:
    node = MemoryRetrievalNode(
        memory_service=FakeMemoryService(),
        task_service=FakeTaskService(),
    )
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="again stuck",
    )

    result = node.run(state)

    assert result.active_tasks[0]["task_id"] == "task-1"


def test_memory_update_node_persists_extracted_memories_through_memory_service() -> None:
    memory_service = FakeMemoryService()
    node = MemoryUpdateNode(memory_service=memory_service)
    memory = Memory(
        memory_id="memory-new",
        user_id="user-1",
        type="emotion_event",
        event="今天写项目文档时拖延",
        emotion="焦虑",
        trigger="任务压力",
        behavior="刷视频回避",
        result="进度中断",
        confidence=0.86,
    )
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="今天写项目文档时拖延",
        new_memories=[memory],
    )

    result = node.run(state)

    assert memory_service.added_memories == [memory]
    assert result.memory_update_result == "success"
