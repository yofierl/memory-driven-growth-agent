from app.agent.graph import GrowthAgentGraph
from app.agent.state import GrowthAgentState
from app.models.memory import Memory
from app.models.pattern import Pattern


class GraphLLMStub:
    def generate_reply(
        self,
        *,
        system_prompt: str | None = None,
        user_message: str,
        conversation_messages: list[dict],
    ):
        return "收到，我继续陪你理清这件事。"

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        if "missing_fields" in system_prompt or "gap_detection" in system_prompt:
            if "信息不全" in user_prompt:
                return {"detected_emotion": "焦虑", "missing_fields": ["trigger"]}
            return {"detected_emotion": "焦虑", "missing_fields": []}
        if "response_planner" in system_prompt:
            strategy = (
                "information_follow_up"
                if "need_follow_up=True" in user_prompt
                else "emotional_support"
            )
            return {"response_strategy": strategy}
        if "new_memories" in system_prompt:
            return {"new_memories": []}
        if "patterns" in system_prompt:
            return {
                "patterns": [
                    {
                        "scenario": "学习",
                        "trigger": "任务压力",
                        "emotion": "焦虑",
                        "behavior": "刷视频回避",
                        "result": "进度中断",
                        "confidence": 0.8,
                    }
                ]
            }
        return {}


class GraphMemoryServiceStub:
    def __init__(self) -> None:
        self.list_calls: list[dict[str, object]] = []

    def search_memories(self, query: str, filters: dict | None = None, top_k: int = 3):
        return []

    def add_memory(self, memory: Memory) -> Memory:
        return memory

    def list_memories(self, user_id: str, filters: dict | None = None):
        self.list_calls.append({"user_id": user_id, "filters": filters})
        return [
            Memory(
                memory_id="m1",
                user_id=user_id,
                type="emotion_event",
                scenario="学习",
                event="事件1",
                emotion="焦虑",
                trigger="任务压力",
                behavior="刷视频回避",
                result="进度中断",
                confidence=0.9,
            ),
            Memory(
                memory_id="m2",
                user_id=user_id,
                type="emotion_event",
                scenario="学习",
                event="事件2",
                emotion="焦虑",
                trigger="任务压力",
                behavior="刷视频回避",
                result="进度中断",
                confidence=0.9,
            ),
            Memory(
                memory_id="m3",
                user_id=user_id,
                type="emotion_event",
                scenario="学习",
                event="事件3",
                emotion="焦虑",
                trigger="任务压力",
                behavior="刷视频回避",
                result="进度中断",
                confidence=0.9,
            ),
        ]


class GraphPatternRepoStub:
    def __init__(self) -> None:
        self.patterns = {}
        self.signature_calls: list[dict[str, object]] = []

    def get_detected_by_signature(
        self,
        *,
        user_id: str,
        scenario: str | None,
        trigger: str,
        emotion: str,
        behavior: str,
    ):
        self.signature_calls.append(
            {
                "user_id": user_id,
                "scenario": scenario,
                "trigger": trigger,
                "emotion": emotion,
                "behavior": behavior,
            }
        )
        return None

    def upsert(self, pattern: Pattern):
        self.patterns[pattern.pattern_id] = pattern
        return pattern


def test_growth_agent_graph_skips_pattern_discovery_during_follow_up() -> None:
    memory_service = GraphMemoryServiceStub()
    graph = GrowthAgentGraph(
        llm_service=GraphLLMStub(),
        memory_service=memory_service,
        pattern_repo=GraphPatternRepoStub(),
    )

    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="信息不全，我只想说最近很焦虑",
    )
    result = graph.run(state)

    assert result.need_follow_up is True
    assert result.detected_patterns == []
    assert memory_service.list_calls == []


def test_growth_agent_graph_runs_pattern_discovery_after_memory_update() -> None:
    memory_service = GraphMemoryServiceStub()
    pattern_repo = GraphPatternRepoStub()
    graph = GrowthAgentGraph(
        llm_service=GraphLLMStub(),
        memory_service=memory_service,
        pattern_repo=pattern_repo,
    )

    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="我最近又因为任务压力刷视频拖延",
    )
    result = graph.run(state)

    assert result.need_follow_up is False
    assert len(result.detected_patterns) == 1
    assert len(result.detected_patterns[0]["evidence_memory_ids"]) >= 3
    assert result.pattern_confirmation_required is True
    assert result.recommended_method is None
    assert result.assistant_response is not None
    assert "确认" in result.assistant_response
    assert "拒绝" in result.assistant_response
    assert memory_service.list_calls == [
        {"user_id": "user-1", "filters": {"type": "emotion_event"}}
    ]
    assert len(pattern_repo.signature_calls) == 1


def test_route_after_memory_update_skips_pattern_discovery_during_follow_up() -> None:
    graph = GrowthAgentGraph(
        llm_service=GraphLLMStub(),
        memory_service=GraphMemoryServiceStub(),
        pattern_repo=GraphPatternRepoStub(),
    )

    route = graph._route_after_memory_update(
        GrowthAgentState(
            user_id="user-1",
            conversation_id="conv-1",
            user_input="继续追问",
            need_follow_up=True,
        )
    )

    assert route == "end"
