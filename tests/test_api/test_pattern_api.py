from fastapi.testclient import TestClient

from app.main import create_app
from app.models.pattern import Pattern


class InMemoryPatternRepo:
    def __init__(self) -> None:
        self.patterns: dict[str, Pattern] = {}

    def list_by_user_id(self, user_id: str, statuses: list[str] | None = None):
        results = [pattern for pattern in self.patterns.values() if pattern.user_id == user_id]
        if statuses is not None:
            results = [pattern for pattern in results if pattern.status in statuses]
        return sorted(results, key=lambda item: item.created_at, reverse=True)

    def get_by_pattern_id(self, pattern_id: str):
        return self.patterns.get(pattern_id)

    def upsert(self, pattern: Pattern):
        self.patterns[pattern.pattern_id] = pattern
        return pattern

    def update_status(self, pattern_id: str, status: str):
        pattern = self.patterns[pattern_id]
        updated = pattern.model_copy(update={"status": status})
        self.patterns[pattern_id] = updated
        return updated


def build_pattern(*, pattern_id: str, status: str = "detected") -> Pattern:
    return Pattern(
        pattern_id=pattern_id,
        user_id="user-1",
        scenario="学习",
        trigger="任务压力",
        emotion="焦虑",
        behavior="刷视频回避",
        result="进度中断",
        frequency=3,
        evidence_memory_ids=["m1", "m2", "m3"],
        confidence=0.81,
        status=status,
    )


def test_list_patterns_returns_detected_and_confirmed_patterns() -> None:
    app = create_app()
    repo = InMemoryPatternRepo()
    repo.upsert(build_pattern(pattern_id="pattern-detected", status="detected"))
    repo.upsert(build_pattern(pattern_id="pattern-confirmed", status="confirmed"))
    repo.upsert(build_pattern(pattern_id="pattern-rejected", status="rejected"))
    app.state.test_pattern_repo = repo
    client = TestClient(app)

    response = client.get("/api/patterns", params={"user_id": "user-1"})

    assert response.status_code == 200
    payload = response.json()
    assert [item["pattern_id"] for item in payload["patterns"]] == [
        "pattern-confirmed",
        "pattern-detected",
    ]
    assert all(len(item["evidence_memory_ids"]) >= 3 for item in payload["patterns"])


def test_pattern_feedback_updates_status() -> None:
    app = create_app()
    repo = InMemoryPatternRepo()
    repo.upsert(build_pattern(pattern_id="pattern-1", status="detected"))
    app.state.test_pattern_repo = repo
    client = TestClient(app)

    response = client.post(
        "/api/patterns/pattern-1/feedback",
        params={"user_id": "user-1"},
        json={"status": "rejected"},
    )

    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert repo.get_by_pattern_id("pattern-1").status == "rejected"


def test_pattern_feedback_returns_404_for_missing_pattern() -> None:
    app = create_app()
    app.state.test_pattern_repo = InMemoryPatternRepo()
    client = TestClient(app)

    response = client.post(
        "/api/patterns/missing/feedback",
        params={"user_id": "user-1"},
        json={"status": "confirmed"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "pattern_not_found"
