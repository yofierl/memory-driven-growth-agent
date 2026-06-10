from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from pymongo import MongoClient

from app.api.chat_api import get_mongo_client
from app.core.exceptions import PatternNotFoundError
from app.repositories.pattern_repo import PatternRepository
from app.schemas.pattern_schema import MutationResponse, PatternFeedbackRequest, PatternListResponse

router = APIRouter(prefix="/api/patterns", tags=["patterns"])


def get_pattern_repo(
    request: Request,
    client: Annotated[MongoClient, Depends(get_mongo_client)],
) -> PatternRepository:
    override = getattr(request.app.state, "test_pattern_repo", None)
    if override is not None:
        return override
    db = client[request.app.state.settings.mongodb_database]
    return PatternRepository(db.patterns)


PatternRepoDep = Annotated[PatternRepository, Depends(get_pattern_repo)]


@router.get("", response_model=PatternListResponse)
async def list_patterns(
    user_id: str = Query(min_length=1),
    pattern_repo: PatternRepoDep = None,
) -> PatternListResponse:
    assert pattern_repo is not None
    patterns = pattern_repo.list_by_user_id(user_id=user_id, statuses=["detected", "confirmed"])
    payload = [pattern.model_dump(mode="json") for pattern in patterns]
    return PatternListResponse(patterns=payload)


@router.post("/{pattern_id}/feedback", response_model=MutationResponse)
async def submit_pattern_feedback(
    pattern_id: str,
    request: PatternFeedbackRequest,
    user_id: str = Query(min_length=1),
    pattern_repo: PatternRepoDep = None,
) -> MutationResponse:
    assert pattern_repo is not None
    pattern = pattern_repo.get_by_pattern_id(pattern_id)
    if pattern is None or pattern.user_id != user_id:
        raise PatternNotFoundError(f"Pattern not found: {pattern_id}")
    pattern_repo.update_status(pattern_id=pattern_id, status=request.status)
    return MutationResponse(success=True)
