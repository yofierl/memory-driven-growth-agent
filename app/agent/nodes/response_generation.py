from __future__ import annotations

from app.agent.state import GrowthAgentState
from app.core.prompt_loader import PromptLoader


class ResponseGenerationNode:
    def __init__(self, llm_service, prompt_loader: PromptLoader | None = None) -> None:
        self.llm_service = llm_service
        self.prompt_loader = prompt_loader or PromptLoader()

    def run(self, state: GrowthAgentState) -> GrowthAgentState:
        system_prompt = self.prompt_loader.load("response_generation")
        history_lines = []
        for msg in state.short_term_messages[-6:]:
            role_label = "用户" if msg.get("role") == "user" else "助手"
            history_lines.append(f"{role_label}：{msg.get('content', '')}")
        history_block = "\n".join(history_lines)
        memory_lines = []
        for memory in state.retrieved_memories[:3]:
            memory_lines.append(
                "；".join(
                    str(value)
                    for value in (
                        memory.get("scenario"),
                        memory.get("event"),
                        memory.get("emotion"),
                        memory.get("trigger"),
                        memory.get("behavior"),
                        memory.get("result"),
                    )
                    if value
                )
            )
        memory_block = "\n".join(f"- {line}" for line in memory_lines if line)

        user_prompt = (
            ("对话历史：\n" + history_block + "\n\n" if history_block else "")
            + f"用户当前输入：{state.user_input}\n"
            + ("相关历史记忆：\n" + memory_block + "\n" if memory_block else "相关历史记忆：无\n")
            + f"已识别情绪：{state.detected_emotion or '未知'}\n"
            + f"缺失字段：{state.missing_fields}\n"
            + f"回复策略：{state.response_strategy}\n"
            + "请按策略生成回复。"
        )
        assistant_response = self.llm_service.generate_reply(
            system_prompt=system_prompt,
            user_message=user_prompt,
            conversation_messages=[],
        )
        state.assistant_response = assistant_response
        return state
