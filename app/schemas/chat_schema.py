from typing import Any

from pydantic import BaseModel, Field

from app.schemas.memory_schema import MemoryResponse


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1)
    conversation_id: str | None = None
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    conversation_id: str
    assistant_response: str
    strategy: str
    risk_level: str = "none"
    risk_reason: str | None = None
    safety_handled: bool = False
    retrieved_memories: list[dict[str, Any]] = Field(default_factory=list)
    detected_patterns: list[dict[str, Any]] = Field(default_factory=list)
    generated_task: dict[str, Any] | None = None


class SimpleChatResponse(BaseModel):
    conversation_id: str
    assistant_response: str
    strategy: str
    stored_memory_count: int
    memories: list[MemoryResponse] = Field(default_factory=list)
