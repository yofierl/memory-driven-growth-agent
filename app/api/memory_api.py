from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.chat_api import get_memory_repo
from app.core.exceptions import FeatureNotImplementedError
from app.repositories.memory_repo import MemoryRepository
from app.schemas.memory_schema import MemoryListResponse, MemoryUpdateRequest, MutationResponse

router = APIRouter(prefix="/api/memories", tags=["memories"])

MemoryRepoDep = Annotated[MemoryRepository, Depends(get_memory_repo)]


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
async def update_memory(memory_id: str, _: MemoryUpdateRequest) -> MutationResponse:
    raise FeatureNotImplementedError(f"Memory update is not implemented for {memory_id}")


@router.delete("/{memory_id}", response_model=MutationResponse)
async def delete_memory(memory_id: str) -> MutationResponse:
    raise FeatureNotImplementedError(f"Memory delete is not implemented for {memory_id}")
