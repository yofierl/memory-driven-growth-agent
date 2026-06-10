from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class Pattern(BaseModel):
    pattern_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    scenario: str | None = None
    trigger: str = Field(min_length=1)
    emotion: str = Field(min_length=1)
    behavior: str = Field(min_length=1)
    result: str = Field(min_length=1)
    frequency: int = Field(ge=3)
    evidence_memory_ids: list[str] = Field(min_length=3)
    confidence: float = Field(ge=0.0, le=1.0)
    status: Literal["detected", "confirmed", "rejected"] = "detected"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
