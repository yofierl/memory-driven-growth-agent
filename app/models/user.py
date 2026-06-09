from datetime import UTC, datetime

from pydantic import BaseModel, Field


class User(BaseModel):
    user_id: str = Field(min_length=1)
    nickname: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
