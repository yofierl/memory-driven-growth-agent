from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class Memory(BaseModel):
    memory_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    type: Literal["emotion_event", "goal", "preference", "reflection"]
    scenario: str | None = None
    event: str | None = None
    emotion: str | None = None
    trigger: str | None = None
    behavior: str | None = None
    result: str | None = None
    importance: int = Field(default=3, ge=1, le=5)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: Literal["conversation", "checkin", "reflection"] = "conversation"
    embedding_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
