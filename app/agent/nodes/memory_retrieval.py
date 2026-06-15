from __future__ import annotations

from app.agent.state import GrowthAgentState


class MemoryRetrievalNode:
    def __init__(self, memory_service, task_service=None) -> None:
        self.memory_service = memory_service
        self.task_service = task_service

    def run(self, state: GrowthAgentState) -> GrowthAgentState:
        memories = self.memory_service.search_memories(
            query=state.user_input,
            filters={"user_id": state.user_id},
            top_k=3,
        )
        state.retrieved_memories = [memory.model_dump(mode="json") for memory in memories]
        if self.task_service is not None:
            tasks = self.task_service.list_active_tasks(state.user_id)
            state.active_tasks = [
                task.model_dump(mode="json") if hasattr(task, "model_dump") else dict(task)
                for task in tasks
            ]
        return state
