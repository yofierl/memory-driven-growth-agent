from app.agent.nodes.pattern_discovery import PatternDiscoveryNode
from app.agent.state import GrowthAgentState
from app.models.memory import Memory
from app.models.pattern import Pattern


class PatternDiscoveryMemoryServiceStub:
    def __init__(self, memories: list[Memory]) -> None:
        self.memories = memories
        self.calls: list[dict[str, object]] = []

    def list_memories(self, user_id: str, filters: dict | None = None):
        self.calls.append({"user_id": user_id, "filters": filters})
        return self.memories


class PatternDiscoveryLLMStub:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.calls: list[dict[str, str]] = []

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        self.calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
        return self.result


class PatternServiceStub:
    def __init__(self, patterns: list[Pattern]) -> None:
        self.patterns = patterns
        self.calls: list[dict[str, object]] = []

    def discover_patterns(
        self,
        *,
        user_id: str,
        memories: list[Memory],
        llm_service,
    ) -> list[Pattern]:
        self.calls.append({"user_id": user_id, "memories": memories, "llm_service": llm_service})
        return self.patterns


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
        confidence=0.86,
    )


def make_pattern(pattern_id: str, *, status: str = "detected") -> Pattern:
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
        confidence=0.88,
        status=status,
    )


def test_pattern_discovery_node_skips_when_follow_up_needed() -> None:
    node = PatternDiscoveryNode(
        llm_service=PatternDiscoveryLLMStub({}),
        memory_service=PatternDiscoveryMemoryServiceStub([make_memory("m1")]),
        pattern_service=PatternServiceStub([make_pattern("pattern-1")]),
    )
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="我最近又拖延了",
        need_follow_up=True,
    )

    result = node.run(state)

    assert result.detected_patterns == []
    assert result.pattern_confirmation_required is False


def test_pattern_discovery_node_attaches_detected_patterns_when_candidate_exists() -> None:
    memory_service = PatternDiscoveryMemoryServiceStub(
        [make_memory("m1"), make_memory("m2"), make_memory("m3")]
    )
    llm_service = PatternDiscoveryLLMStub({})
    pattern_service = PatternServiceStub([make_pattern("pattern-1")])
    node = PatternDiscoveryNode(
        llm_service=llm_service,
        memory_service=memory_service,
        pattern_service=pattern_service,
    )
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="我最近又拖延了",
        need_follow_up=False,
    )

    result = node.run(state)

    assert memory_service.calls == [{"user_id": "user-1", "filters": {"type": "emotion_event"}}]
    assert len(result.detected_patterns) == 1
    assert result.detected_patterns[0]["pattern_id"] == "pattern-1"
    assert len(result.detected_patterns[0]["evidence_memory_ids"]) >= 3
    assert result.pattern_confirmation_required is True


def test_pattern_discovery_node_no_candidate_keeps_confirmation_false() -> None:
    node = PatternDiscoveryNode(
        llm_service=PatternDiscoveryLLMStub({}),
        memory_service=PatternDiscoveryMemoryServiceStub(
            [make_memory("m1"), make_memory("m2"), make_memory("m3")]
        ),
        pattern_service=PatternServiceStub([]),
    )
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="我最近又拖延了",
        need_follow_up=False,
    )

    result = node.run(state)

    assert result.detected_patterns == []
    assert result.pattern_confirmation_required is False
