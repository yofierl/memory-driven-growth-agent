from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.agent.state import GrowthAgentState
from app.core.prompt_loader import PromptLoader


@dataclass(frozen=True)
class KeywordSignal:
    level: Literal["L1", "L2", "none"]
    reason: str | None = None


class RiskDetectionNode:
    l1_keywords = (
        "hurt myself",
        "kill myself",
        "suicide",
        "end my life",
        "harm someone",
        "kill someone",
        "自杀",
        "自残",
        "伤害别人",
        "结束生命",
    )
    l2_keywords = (
        "不想活",
        "杀了",
        "今晚就",
    )

    def __init__(self, llm_service, prompt_loader: PromptLoader | None = None) -> None:
        self.llm_service = llm_service
        self.prompt_loader = prompt_loader or PromptLoader()

    def run(self, state: GrowthAgentState) -> GrowthAgentState:
        keyword_signal = self._keyword_signal(state.user_input)
        system_prompt = self.prompt_loader.load("risk_detection")
        history_lines = [
            f"{message.get('role', 'unknown')}: {message.get('content', '')}"
            for message in state.short_term_messages[-6:]
        ]
        history_block = (
            "Recent conversation:\n" + "\n".join(history_lines) + "\n\n" if history_lines else ""
        )
        prior_line = (
            f"Prior keyword signal: {keyword_signal.level}"
            + (f" ({keyword_signal.reason})" if keyword_signal.reason else "")
            + "\n"
        )
        user_prompt = history_block + prior_line + f"Current user input:\n{state.user_input}"
        result = self.llm_service.structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        risk_level = result.get("risk_level", "none")
        if risk_level not in {"none", "low", "medium", "high"}:
            risk_level = "none"
        state.risk_level = risk_level
        risk_reason = result.get("risk_reason")
        state.risk_reason = risk_reason if isinstance(risk_reason, str) else None
        return state

    def _keyword_signal(self, text: str) -> KeywordSignal:
        normalized = text.lower()
        for keyword in self.l1_keywords:
            if keyword.lower() in normalized:
                return KeywordSignal("L1", f"Matched keyword: {keyword}")
        for keyword in self.l2_keywords:
            if keyword.lower() in normalized:
                return KeywordSignal("L2", f"Matched keyword: {keyword}")
        return KeywordSignal("none")
