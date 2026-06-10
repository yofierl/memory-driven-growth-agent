from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.memory import Memory


class GrowthAgentState(BaseModel):
    user_id: str = Field(min_length=1)
    conversation_id: str = Field(min_length=1)
    user_input: str = Field(min_length=1)
    short_term_messages: list[dict] = Field(default_factory=list)
    assistant_response: str | None = None
    detected_emotion: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    need_follow_up: bool = False
    response_strategy: Literal["emotional_support", "information_follow_up"] | None = None
    retrieved_memories: list[dict] = Field(default_factory=list)
    new_memories: list[Memory] = Field(default_factory=list)
    memory_update_result: str | None = None
    detected_patterns: list[dict[str, Any]] = Field(default_factory=list)
    pattern_confirmation_required: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
