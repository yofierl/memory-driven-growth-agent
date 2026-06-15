from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from pymongo import MongoClient

from app.api.chat_api import get_mongo_client
from app.core.exceptions import TaskNotFoundError
from app.repositories.task_repo import TaskRepository
from app.schemas.task_schema import MutationResponse, TaskListResponse, TaskStatusUpdateRequest
from app.services.task_service import TaskService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def get_task_repo(
    request: Request,
    client: Annotated[MongoClient, Depends(get_mongo_client)],
) -> TaskRepository:
    override = getattr(request.app.state, "test_task_repo", None)
    if override is not None:
        return override
    db = client[request.app.state.settings.mongodb_database]
    return TaskRepository(db.tasks)


def get_task_service(
    request: Request, task_repo: Annotated[TaskRepository, Depends(get_task_repo)]
) -> TaskService:
    override = getattr(request.app.state, "test_task_service", None)
    if override is not None:
        return override
    llm_service = getattr(request.app.state, "test_llm_service", None) or getattr(
        request.app.state, "llm_service", None
    )
    return TaskService(llm_service=llm_service, task_repo=task_repo)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
TaskRepoDep = Annotated[TaskRepository, Depends(get_task_repo)]


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    user_id: str = Query(min_length=1),
    task_service: TaskServiceDep = None,
) -> TaskListResponse:
    assert task_service is not None
    tasks = task_service.list_tasks(user_id=user_id)
    return TaskListResponse(tasks=[task.model_dump(mode="json") for task in tasks])


@router.post("/{task_id}/status", response_model=MutationResponse)
async def update_task_status(
    task_id: str,
    request: TaskStatusUpdateRequest,
    user_id: str = Query(min_length=1),
    task_repo: TaskRepoDep = None,
    task_service: TaskServiceDep = None,
) -> MutationResponse:
    assert task_repo is not None
    assert task_service is not None
    task = task_repo.get_by_task_id(task_id)
    if task is None or task.user_id != user_id:
        raise TaskNotFoundError(f"Task not found: {task_id}")
    task_service.update_task_status(
        task_id=task_id, status=request.status, feedback=request.feedback
    )
    return MutationResponse(success=True)
