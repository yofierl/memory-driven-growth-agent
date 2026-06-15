from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.chat_api import get_memory_repo, get_memory_service
from app.core.exceptions import MemoryNotFoundError
from app.repositories.memory_repo import MemoryRepository
from app.schemas.memory_schema import MemoryListResponse, MemoryUpdateRequest, MutationResponse
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/api/memories", tags=["memories"])

MemoryRepoDep = Annotated[MemoryRepository, Depends(get_memory_repo)]
MemoryServiceDep = Annotated[MemoryService, Depends(get_memory_service)]


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    user_id: str = Query(min_length=1),
    type: str | None = Query(default=None),
    memory_repo: MemoryRepoDep = None,
) -> MemoryListResponse:
    assert memory_repo is not None
    memories = memory_repo.list_by_user_id(user_id=user_id, memory_type=type)
    payload = [memory.model_dump(mode="json") for memory in memories]
    return MemoryListResponse(memories=payload)


@router.patch("/{memory_id}", response_model=MutationResponse)
async def update_memory(
    memory_id: str,
    request: MemoryUpdateRequest,
    user_id: str = Query(min_length=1),
    memory_repo: MemoryRepoDep = None,
    memory_service: MemoryServiceDep = None,
) -> MutationResponse:
    assert memory_repo is not None
    assert memory_service is not None
    memory = memory_repo.get_by_id(memory_id)
    if memory is None or memory.user_id != user_id:
        raise MemoryNotFoundError(f"Memory not found: {memory_id}")
    patch = request.model_dump(exclude_none=True)
    try:
        memory_service.update_memory(memory_id=memory_id, patch=patch)
    except KeyError:
        raise MemoryNotFoundError(f"Memory not found: {memory_id}") from None
    return MutationResponse(success=True)


@router.delete("/{memory_id}", response_model=MutationResponse)
async def delete_memory(
    memory_id: str,
    user_id: str = Query(min_length=1),
    memory_repo: MemoryRepoDep = None,
    memory_service: MemoryServiceDep = None,
) -> MutationResponse:
    assert memory_repo is not None
    assert memory_service is not None
    memory = memory_repo.get_by_id(memory_id)
    if memory is None or memory.user_id != user_id:
        raise MemoryNotFoundError(f"Memory not found: {memory_id}")
    deleted = memory_service.delete_memory(memory_id=memory_id)
    if not deleted:
        raise MemoryNotFoundError(f"Memory not found: {memory_id}")
    return MutationResponse(success=True)
