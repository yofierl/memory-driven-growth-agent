from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TaskResponse(BaseModel):
    task_id: str
    user_id: str
    task_content: str
    status: Literal["pending", "completed", "failed", "adjusted"]
    method_id: str | None = None
    feedback: str | None = None
    created_at: datetime | None = None
    due_at: datetime | None = None
    updated_at: datetime | None = None


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse] = Field(default_factory=list)


class TaskStatusUpdateRequest(BaseModel):
    status: Literal["completed", "failed"]
    feedback: str | None = None


class MutationResponse(BaseModel):
    success: bool
