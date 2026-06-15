from datetime import UTC, datetime

from app.models.memory import Memory
from app.models.pattern import Pattern
from app.services.pattern_service import PatternService


class PatternRepoStub:
    def __init__(self) -> None:
        self.saved_patterns = []
        self.existing_by_signature = {}
        self.last_signature_query: dict[str, object] | None = None

    def get_detected_by_signature(
        self,
        *,
        user_id: str,
        scenario: str | None,
        trigger: str,
        emotion: str,
        behavior: str,
    ):
        self.last_signature_query = {
            "user_id": user_id,
            "scenario": scenario,
            "trigger": trigger,
            "emotion": emotion,
            "behavior": behavior,
        }
        return self.existing_by_signature.get((user_id, scenario, trigger, emotion, behavior))

    def upsert(self, pattern):
        self.saved_patterns.append(pattern)
        return pattern


class PatternLLMStub:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls = []

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        self.calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
        return self.response


def make_memory(memory_id: str, *, scenario: str = "学习") -> Memory:
    return Memory(
        memory_id=memory_id,
        user_id="user-1",
        type="emotion_event",
        scenario=scenario,
        event=f"事件-{memory_id}",
        emotion="焦虑",
        trigger="任务压力",
        behavior="刷视频回避",
        result="进度中断",
        confidence=0.82,
    )


def make_pattern(
    pattern_id: str,
    *,
    status: str = "detected",
    frequency: int = 3,
) -> Pattern:
    timestamp = datetime.now(UTC)
    return Pattern(
        pattern_id=pattern_id,
        user_id="user-1",
        scenario="学习",
        trigger="任务压力",
        emotion="焦虑",
        behavior="刷视频回避",
        result="进度中断",
        frequency=frequency,
        evidence_memory_ids=["m1", "m2", "m3"],
        confidence=0.78,
        status=status,
        created_at=timestamp,
        updated_at=timestamp,
    )


def test_discover_patterns_requires_three_distinct_evidence_memory_ids() -> None:
    repo = PatternRepoStub()
    service = PatternService(pattern_repo=repo)
    llm_service = PatternLLMStub(
        {
            "patterns": [
                {
                    "scenario": "学习",
                    "trigger": "任务压力",
                    "emotion": "焦虑",
                    "behavior": "刷视频回避",
                    "result": "进度中断",
                    "confidence": 0.84,
                }
            ]
        }
    )

    result = service.discover_patterns(
        user_id="user-1",
        memories=[make_memory("m1"), make_memory("m2")],
        llm_service=llm_service,
    )

    assert result == []
    assert repo.saved_patterns == []


def test_discover_patterns_persists_detected_pattern_with_evidence() -> None:
    repo = PatternRepoStub()
    service = PatternService(pattern_repo=repo)
    llm_service = PatternLLMStub(
        {
            "patterns": [
                {
                    "scenario": "学习",
                    "trigger": "任务压力",
                    "emotion": "焦虑",
                    "behavior": "刷视频回避",
                    "result": "进度中断",
                    "confidence": 0.84,
                }
            ]
        }
    )

    result = service.discover_patterns(
        user_id="user-1",
        memories=[make_memory("m1"), make_memory("m2"), make_memory("m3")],
        llm_service=llm_service,
    )

    assert len(result) == 1
    assert result[0].frequency == 3
    assert result[0].status == "detected"
    assert result[0].evidence_memory_ids == ["m1", "m2", "m3"]
    assert repo.saved_patterns[0].pattern_id == result[0].pattern_id


def test_discover_patterns_groups_by_trigger_emotion_behavior_chain() -> None:
    repo = PatternRepoStub()
    service = PatternService(pattern_repo=repo)
    llm_service = PatternLLMStub({"patterns": []})

    service.discover_patterns(
        user_id="user-1",
        memories=[
            make_memory("m1", scenario="学习"),
            make_memory("m2", scenario="学习"),
            make_memory("m3", scenario="学习"),
            make_memory("m4", scenario="面试"),
        ],
        llm_service=llm_service,
    )

    prompt = llm_service.calls[0]["user_prompt"]
    assert all(memory_id in prompt for memory_id in ("m1", "m2", "m3", "m4"))


def test_normalization_groups_synonyms_for_pattern_evidence() -> None:
    repo = PatternRepoStub()
    service = PatternService(pattern_repo=repo)
    llm_service = PatternLLMStub(
        {
            "patterns": [
                {
                    "scenario": "学习",
                    "trigger": "任务压力",
                    "emotion": "焦虑",
                    "behavior": "拖延回避",
                    "result": "进度中断",
                    "confidence": 0.86,
                }
            ]
        }
    )

    memories = [
        make_memory("m1").model_copy(
            update={"emotion": "焦虑", "trigger": "任务压力", "behavior": "刷视频"}
        ),
        make_memory("m2").model_copy(
            update={"emotion": "慌", "trigger": "任务压力", "behavior": "看短视频"}
        ),
        make_memory("m3").model_copy(
            update={"emotion": "压力很大", "trigger": "任务压力", "behavior": "刷B站"}
        ),
    ]

    result = service.discover_patterns(
        user_id="user-1",
        memories=memories,
        llm_service=llm_service,
    )

    assert len(result) == 1
    assert result[0].evidence_memory_ids == ["m1", "m2", "m3"]


def test_discover_patterns_reuses_existing_pattern_id() -> None:
    repo = PatternRepoStub()
    existing = make_pattern("pattern-existing", frequency=4)
    repo.existing_by_signature[("user-1", "学习", "任务压力", "焦虑", "刷视频回避")] = existing
    service = PatternService(pattern_repo=repo)
    llm_service = PatternLLMStub(
        {
            "patterns": [
                {
                    "scenario": "学习",
                    "trigger": "任务压力",
                    "emotion": "焦虑",
                    "behavior": "刷视频回避",
                    "result": "进度中断",
                    "confidence": 0.91,
                }
            ]
        }
    )

    result = service.discover_patterns(
        user_id="user-1",
        memories=[make_memory("m1"), make_memory("m2"), make_memory("m3")],
        llm_service=llm_service,
    )

    assert len(result) == 1
    assert result[0].pattern_id == "pattern-existing"
    assert repo.saved_patterns[0].pattern_id == "pattern-existing"


def test_discover_patterns_skips_rejected_existing_pattern() -> None:
    repo = PatternRepoStub()
    rejected = make_pattern("pattern-rejected", status="rejected")
    repo.existing_by_signature[("user-1", "学习", "任务压力", "焦虑", "刷视频回避")] = rejected
    service = PatternService(pattern_repo=repo)
    llm_service = PatternLLMStub(
        {
            "patterns": [
                {
                    "scenario": "学习",
                    "trigger": "任务压力",
                    "emotion": "焦虑",
                    "behavior": "刷视频回避",
                    "result": "进度中断",
                    "confidence": 0.84,
                }
            ]
        }
    )

    result = service.discover_patterns(
        user_id="user-1",
        memories=[make_memory("m1"), make_memory("m2"), make_memory("m3")],
        llm_service=llm_service,
    )

    assert result == []
    assert repo.saved_patterns == []


def test_discover_patterns_preserves_confirmed_status_on_merge() -> None:
    repo = PatternRepoStub()
    existing_confirmed = Pattern(
        pattern_id="pattern-existing",
        user_id="user-1",
        scenario="学习",
        trigger="任务压力",
        emotion="焦虑",
        behavior="刷视频回避",
        result="进度中断",
        frequency=4,
        evidence_memory_ids=["m1", "m2", "m3", "m4"],
        confidence=0.82,
        status="confirmed",
    )
    repo.existing_by_signature[("user-1", "学习", "任务压力", "焦虑", "刷视频回避")] = (
        existing_confirmed
    )

    class LLMStub:
        def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
            return {
                "patterns": [
                    {
                        "trigger": "任务压力",
                        "emotion": "焦虑",
                        "behavior": "刷视频回避",
                        "result": "进度中断",
                        "confidence": 0.83,
                    }
                ]
            }

    service = PatternService(pattern_repo=repo)
    memories = [
        make_memory("m1"),
        make_memory("m2"),
        make_memory("m3"),
        make_memory("m4"),
    ]
    result = service.discover_patterns(user_id="user-1", memories=memories, llm_service=LLMStub())

    assert len(result) == 1
    assert result[0].status == "confirmed"
    assert result[0].pattern_id == "pattern-existing"
    assert result[0].frequency == 4
