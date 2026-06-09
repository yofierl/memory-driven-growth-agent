from fastapi import APIRouter

from app.core.exceptions import FeatureNotImplementedError
from app.schemas.pattern_schema import MutationResponse, PatternFeedbackRequest, PatternListResponse

router = APIRouter(prefix="/api/patterns", tags=["patterns"])


@router.get("", response_model=PatternListResponse)
async def list_patterns() -> PatternListResponse:
    raise FeatureNotImplementedError("Pattern API is not implemented in module 1")


@router.post("/{pattern_id}/feedback", response_model=MutationResponse)
async def submit_pattern_feedback(
    pattern_id: str,
    _: PatternFeedbackRequest,
) -> MutationResponse:
    raise FeatureNotImplementedError(f"Pattern feedback is not implemented for {pattern_id}")
