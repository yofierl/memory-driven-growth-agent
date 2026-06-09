from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PatternResponse(BaseModel):
    pattern_id: str
    user_id: str
    status: Literal["detected", "confirmed", "rejected"]
    trigger: str | None = None
    emotion: str | None = None
    behavior: str | None = None
    result: str | None = None
    frequency: int | None = Field(default=None, ge=0)
    evidence_memory_ids: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PatternListResponse(BaseModel):
    patterns: list[PatternResponse] = Field(default_factory=list)


class PatternFeedbackRequest(BaseModel):
    status: Literal["confirmed", "rejected"]


class MutationResponse(BaseModel):
    success: bool
