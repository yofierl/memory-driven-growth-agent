from __future__ import annotations

import json
import re
from collections.abc import Sequence

import httpx

from app.core.config import Settings, get_settings
from app.core.exceptions import LLMServiceError


class LLMService:
    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.http_client = http_client or httpx.Client(
            timeout=self.settings.agent_node_timeout_seconds
        )

    def generate_reply(
        self,
        *,
        user_message: str,
        conversation_messages: Sequence[dict],
        system_prompt: str | None = None,
    ) -> str:
        if not self.settings.llm_api_key or not self.settings.llm_model:
            return f"我听到你在说：{user_message}。如果你愿意，可以继续具体说说刚刚发生了什么。"
        response_text = self._chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                    or (
                        "You are a calm growth-coaching assistant. "
                        "Give one concise supportive reply."
                    ),
                },
                *list(conversation_messages),
                {"role": "user", "content": user_message},
            ]
        )
        return response_text.strip()

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        if not self.settings.llm_api_key or not self.settings.llm_model:
            return {"new_memories": []}
        response_text = self._chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(self._extract_json(response_text))
        except json.JSONDecodeError as exc:
            raise LLMServiceError("LLM returned invalid JSON for structured extraction") from exc

    def _chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        response_format: dict | None = None,
    ) -> str:
        provider = self.settings.llm_provider.lower()
        if provider not in {"openai", "qwen", "deepseek"}:
            raise LLMServiceError(f"Unsupported LLM provider: {self.settings.llm_provider}")
        base_url = self.settings.llm_base_url or "https://api.openai.com/v1"
        payload: dict[str, object] = {
            "model": self.settings.llm_model,
            "messages": messages,
            "temperature": self.settings.llm_temperature,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        response = self.http_client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        try:
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as exc:
            raise LLMServiceError(f"LLM completion failed: {exc}") from exc

    @staticmethod
    def _extract_json(text: str) -> str:
        match = re.search(r"\{[\s\S]*\}", text)
        return match.group(0) if match else text
