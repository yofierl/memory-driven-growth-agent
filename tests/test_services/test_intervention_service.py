from app.models.method import Method
from app.models.pattern import Pattern
from app.services.intervention_service import InterventionService


def make_method(method_id: str, target_problem: list[str]) -> Method:
    return Method(
        method_id=method_id,
        name=method_id,
        description="test method",
        target_problem=target_problem,
        steps=["start"],
        difficulty="low",
    )


def test_fallback_method_does_not_match_empty_none_text() -> None:
    pattern = Pattern(
        pattern_id="pattern-1",
        user_id="user-1",
        trigger="无",
        emotion="无",
        behavior="无",
        result="无",
        frequency=3,
        evidence_memory_ids=["m1", "m2", "m3"],
        confidence=0.8,
        status="confirmed",
    )
    methods = [
        make_method("method_default", ["任务压力"]),
        make_method("method_acceptance", ["无条件接纳"]),
    ]

    selected = InterventionService._fallback_method(
        latest_pattern=pattern,
        methods=methods,
    )

    assert selected.method_id == "method_default"
