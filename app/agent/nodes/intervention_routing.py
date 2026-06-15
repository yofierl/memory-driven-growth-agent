from __future__ import annotations

from app.agent.state import GrowthAgentState
from app.core.prompt_loader import PromptLoader


class InterventionRoutingNode:
    def __init__(
        self,
        llm_service,
        memory_service,
        intervention_service,
        prompt_loader: PromptLoader | None = None,
    ) -> None:
        self.llm_service = llm_service
        self.memory_service = memory_service
        self.intervention_service = intervention_service
        self.prompt_loader = prompt_loader or PromptLoader()

    def run(self, state: GrowthAgentState) -> GrowthAgentState:
        state.recommended_method = None
        recommendation = self.intervention_service.route_method(
            user_id=state.user_id,
            llm_service=self._llm_adapter(),
        )
        if recommendation is None:
            return state
        state.recommended_method = recommendation
        return state

    def _llm_adapter(self):
        prompt = self.prompt_loader.load("intervention_routing")
        parent = self.llm_service

        class _Adapter:
            def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
                return parent.structured_json(
                    system_prompt=prompt + "\n\n" + system_prompt,
                    user_prompt=user_prompt,
                )

        return _Adapter()
