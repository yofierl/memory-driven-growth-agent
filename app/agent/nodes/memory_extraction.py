from __future__ import annotations

from uuid import uuid4

from app.agent.state import GrowthAgentState
from app.core.prompt_loader import PromptLoader
from app.models.memory import Memory


class MemoryExtractionNode:
    def __init__(self, llm_service, prompt_loader: PromptLoader | None = None) -> None:
        self.llm_service = llm_service
        self.prompt_loader = prompt_loader or PromptLoader()

    def run(self, state: GrowthAgentState) -> GrowthAgentState:
        system_prompt = self.prompt_loader.load("memory_extraction")
        user_prompt = (
            f"用户输入：{state.user_input}\n"
            f"助手回复：{state.assistant_response or ''}\n"
            "请提取值得长期保存的结构化记忆。"
        )
        result = self.llm_service.structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        parsed_memories: list[Memory] = []
        for item in result.get("new_memories", []):
            confidence = item.get("confidence", 0)
            try:
                confidence_value = float(confidence)
            except (TypeError, ValueError):
                confidence_value = 0.0
            if confidence_value < 0.6:
                continue

            memory_payload = dict(item)
            memory_payload.setdefault("type", "emotion_event")
            memory_payload.setdefault("source", "conversation")
            memory_payload["memory_id"] = memory_payload.get("memory_id") or str(uuid4())
            memory_payload["user_id"] = state.user_id
            parsed_memories.append(Memory.model_validate(memory_payload))
        state.new_memories = parsed_memories
        return state
