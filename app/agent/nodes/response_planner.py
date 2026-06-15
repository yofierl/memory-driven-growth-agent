from __future__ import annotations

from datetime import UTC, datetime

from app.agent.state import GrowthAgentState
from app.core.prompt_loader import PromptLoader


class ResponsePlannerNode:
    def __init__(self, llm_service, prompt_loader: PromptLoader | None = None) -> None:
        self.llm_service = llm_service
        self.prompt_loader = prompt_loader or PromptLoader()

    def run(self, state: GrowthAgentState) -> GrowthAgentState:
        if self._has_overdue_active_task(state):
            state.response_strategy = "task_review"
            return state

        system_prompt = self.prompt_loader.load("response_planner")
        user_prompt = (
            f"用户输入：{state.user_input}\n"
            f"detected_emotion={state.detected_emotion}\n"
            f"missing_fields={state.missing_fields}\n"
            f"need_follow_up={state.need_follow_up}\n"
            "请选择本轮回复策略。"
        )
        result = self.llm_service.structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        strategy = result.get("response_strategy")
        if strategy not in {"emotional_support", "information_follow_up", "task_review"}:
            strategy = "information_follow_up" if state.need_follow_up else "emotional_support"
        state.response_strategy = strategy
        return state

    @staticmethod
    def _has_overdue_active_task(state: GrowthAgentState) -> bool:
        now = datetime.now(UTC)
        for task in state.active_tasks:
            if task.get("status") != "pending":
                continue
            due_at = task.get("due_at")
            if due_at is None:
                continue
            if isinstance(due_at, str):
                try:
                    due_at = datetime.fromisoformat(due_at)
                except ValueError:
                    continue
            if isinstance(due_at, datetime) and due_at < now:
                return True
        return False
