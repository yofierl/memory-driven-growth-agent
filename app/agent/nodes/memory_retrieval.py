from __future__ import annotations

from app.agent.state import GrowthAgentState


class MemoryRetrievalNode:
    def __init__(self, memory_service) -> None:
        self.memory_service = memory_service

    def run(self, state: GrowthAgentState) -> GrowthAgentState:
        memories = self.memory_service.search_memories(
            query=state.user_input,
            filters={"user_id": state.user_id, "type": "emotion_event"},
            top_k=3,
        )
        state.retrieved_memories = [memory.model_dump(mode="json") for memory in memories]
        return state
