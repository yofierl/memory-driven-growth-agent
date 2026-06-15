from __future__ import annotations

from app.agent.state import GrowthAgentState
from app.core.prompt_loader import PromptLoader


class TaskGenerationNode:
    def __init__(self, task_service, prompt_loader: PromptLoader | None = None) -> None:
        self.task_service = task_service
        self.prompt_loader = prompt_loader or PromptLoader()

    def run(self, state: GrowthAgentState) -> GrowthAgentState:
        state.generated_task = None
        if state.recommended_method is None:
            return state
        task = self.task_service.generate_task(
            user_id=state.user_id,
            recommended_method=state.recommended_method,
            llm_adapter=self._llm_adapter(),
        )
        if task is None:
            return state
        state.generated_task = task.model_dump(mode="json")
        state.active_tasks.append(state.generated_task)
        return state

    def _llm_adapter(self):
        task_generation_prompt = self.prompt_loader.load("task_generation")
        parent = self.task_service.llm_service

        class _Adapter:
            def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
                return parent.structured_json(
                    system_prompt=task_generation_prompt + "\n\n" + system_prompt,
                    user_prompt=user_prompt,
                )

        return _Adapter()
