from __future__ import annotations

from app.agent.state import GrowthAgentState


class MemoryUpdateNode:
    def __init__(self, memory_service) -> None:
        self.memory_service = memory_service

    def run(self, state: GrowthAgentState) -> GrowthAgentState:
        if not state.new_memories:
            state.memory_update_result = "skipped"
            return state

        stored_memories = []
        for memory in state.new_memories:
            stored_memories.append(self.memory_service.add_memory(memory))
        state.new_memories = stored_memories
        state.memory_update_result = "success"
        return state
