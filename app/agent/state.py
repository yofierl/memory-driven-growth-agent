from datetime import UTC, datetime

from pydantic import BaseModel, Field

from app.models.memory import Memory


class GrowthAgentState(BaseModel):
    user_id: str = Field(min_length=1)
    conversation_id: str = Field(min_length=1)
    user_input: str = Field(min_length=1)
    assistant_response: str | None = None
    new_memories: list[Memory] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
