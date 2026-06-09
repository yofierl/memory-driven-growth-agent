from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MemoryResponse(BaseModel):
    memory_id: str
    user_id: str
    type: Literal["emotion_event", "goal", "preference", "reflection"]
    scenario: str | None = None
    event: str | None = None
    emotion: str | None = None
    trigger: str | None = None
    behavior: str | None = None
    result: str | None = None
    importance: int | None = Field(default=None, ge=1, le=5)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    source: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MemoryListResponse(BaseModel):
    memories: list[MemoryResponse] = Field(default_factory=list)


class MemoryUpdateRequest(BaseModel):
    scenario: str | None = None
    event: str | None = None
    emotion: str | None = None
    trigger: str | None = None
    behavior: str | None = None
    result: str | None = None
    importance: int | None = Field(default=None, ge=1, le=5)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class MutationResponse(BaseModel):
    success: bool
