from __future__ import annotations

from uuid import uuid4

from app.agent.state import GrowthAgentState
from app.core.prompt_loader import PromptLoader
from app.models.safety_log import SafetyLog


class SafetyResponseNode:
    def __init__(self, safety_log_repo=None, prompt_loader: PromptLoader | None = None) -> None:
        self.safety_log_repo = safety_log_repo
        self.prompt_loader = prompt_loader or PromptLoader()

    def run(self, state: GrowthAgentState) -> GrowthAgentState:
        # The high-risk reply is hardcoded by design; loading the prompt
        # verifies the documented safety policy file exists.
        self.prompt_loader.load("safety_response")
        state.assistant_response = (
            "I am really sorry you are facing this. If you are in immediate danger, "
            "please contact local emergency services now. Please also reach out to a "
            "trusted person nearby or a qualified crisis support service. I cannot "
            "provide crisis intervention or instructions for harm, but your safety "
            "matters more than continuing this coaching flow."
        )
        state.safety_handled = True
        state.retrieved_memories = []
        state.new_memories = []
        state.detected_patterns = []
        state.pattern_confirmation_required = False
        state.recommended_method = None
        state.generated_task = None
        if self.safety_log_repo is not None:
            self.safety_log_repo.insert(
                SafetyLog(
                    safety_log_id=str(uuid4()),
                    user_id=state.user_id,
                    conversation_id=state.conversation_id,
                    risk_level=state.risk_level,
                    risk_reason=state.risk_reason,
                )
            )
        return state
