from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class Task(BaseModel):
    task_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    task_content: str = Field(min_length=1)
    status: Literal["pending", "completed", "failed", "adjusted"] = "pending"
    method_id: str | None = None
    pattern_id: str | None = None
    feedback: str | None = None
    difficulty: Literal["low", "adjusted"] = "low"
    duration_minutes: int | None = Field(default=None, ge=1, le=60)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    due_at: datetime | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
