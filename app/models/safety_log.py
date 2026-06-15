from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class SafetyLog(BaseModel):
    safety_log_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    conversation_id: str = Field(min_length=1)
    risk_level: str = Field(min_length=1)
    risk_reason: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
