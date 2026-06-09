from fastapi import APIRouter

from app.core.exceptions import FeatureNotImplementedError
from app.schemas.task_schema import MutationResponse, TaskListResponse, TaskStatusUpdateRequest

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks() -> TaskListResponse:
    raise FeatureNotImplementedError("Task API is not implemented in module 1")


@router.post("/{task_id}/status", response_model=MutationResponse)
async def update_task_status(task_id: str, _: TaskStatusUpdateRequest) -> MutationResponse:
    raise FeatureNotImplementedError(f"Task status update is not implemented for {task_id}")
