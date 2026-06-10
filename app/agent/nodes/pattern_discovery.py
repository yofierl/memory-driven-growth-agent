from __future__ import annotations

from app.agent.state import GrowthAgentState
from app.core.prompt_loader import PromptLoader


class PatternDiscoveryNode:
    def __init__(
        self,
        llm_service,
        memory_service,
        pattern_service,
        prompt_loader: PromptLoader | None = None,
    ) -> None:
        self.llm_service = llm_service
        self.memory_service = memory_service
        self.pattern_service = pattern_service
        self.prompt_loader = prompt_loader or PromptLoader()

    def run(self, state: GrowthAgentState) -> GrowthAgentState:
        state.detected_patterns = []
        state.pattern_confirmation_required = False
        if state.need_follow_up:
            return state
        if not hasattr(self.memory_service, "list_memories"):
            return state

        memories = self.memory_service.list_memories(
            user_id=state.user_id,
            filters={"type": "emotion_event"},
        )
        patterns = self.pattern_service.discover_patterns(
            user_id=state.user_id,
            memories=memories,
            llm_service=self._llm_adapter(),
        )
        state.detected_patterns = [pattern.model_dump(mode="json") for pattern in patterns]
        state.pattern_confirmation_required = len(state.detected_patterns) > 0
        return state

    def _llm_adapter(self):
        prompt = self.prompt_loader.load("pattern_discovery")
        parent = self.llm_service

        class _Adapter:
            def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
                return parent.structured_json(
                    system_prompt=prompt + "\n\n" + system_prompt,
                    user_prompt=user_prompt,
                )

        return _Adapter()
