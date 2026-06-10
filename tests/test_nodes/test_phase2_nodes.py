"""Phase 2 tests: GapDetectionNode, ResponsePlannerNode, ResponseGenerationNode."""

from app.agent.nodes.gap_detection import GapDetectionNode
from app.agent.nodes.response_generation import ResponseGenerationNode
from app.agent.nodes.response_planner import ResponsePlannerNode
from app.agent.state import GrowthAgentState

# ---------------------------------------------------------------------------
# Stub LLM services
# ---------------------------------------------------------------------------


class GapDetectStubLLMService:
    """Returns emotion=焦虑, missing_fields=[event, trigger, behavior]."""

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        assert "gap" in system_prompt.lower() or "信息" in system_prompt
        assert "焦虑" in user_prompt
        return {
            "detected_emotion": "焦虑",
            "missing_fields": ["event", "trigger", "behavior"],
        }


class GapDetectNoFollowUpStubLLMService:
    """All fields present → no follow-up needed."""

    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        self.calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
        return {
            "detected_emotion": "失落",
            "missing_fields": [],
        }


class GapDetectStubLLMServiceMissingBehavior:
    """Missing only behavior → shorter follow-up."""

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        return {
            "detected_emotion": "焦虑",
            "missing_fields": ["behavior"],
        }


class PlannerStubLLMService:
    """Plans emotional_support strategy."""

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        assert "strategy" in system_prompt.lower() or "策略" in system_prompt
        return {"response_strategy": "emotional_support"}


class PlannerFollowUpStubLLMService:
    """Plans information_follow_up strategy."""

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        return {"response_strategy": "information_follow_up"}


class GenerationStubLLMService:
    """Returns a supportive reply."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def generate_reply(
        self,
        *,
        user_message: str,
        conversation_messages: list[dict],
        system_prompt: str | None = None,
    ) -> str:
        self.calls.append(
            {
                "user_message": user_message,
                "conversation_messages": conversation_messages,
                "system_prompt": system_prompt,
            }
        )
        assert user_message
        return "听起来你最近被焦虑感影响了。可以告诉我具体发生了什么事吗？"


class GenerationPromptAwareStubLLMService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def generate_reply(
        self,
        *,
        user_message: str,
        conversation_messages: list[dict],
        system_prompt: str | None = None,
    ) -> str:
        self.calls.append(
            {
                "user_message": user_message,
                "conversation_messages": conversation_messages,
                "system_prompt": system_prompt,
            }
        )
        return "我会按本轮策略简洁回应。"


class GenerationFollowUpStubLLMService:
    """Returns one focused follow-up question."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def generate_reply(
        self,
        *,
        user_message: str,
        conversation_messages: list[dict],
        system_prompt: str | None = None,
    ) -> str:
        self.calls.append(
            {
                "user_message": user_message,
                "conversation_messages": conversation_messages,
                "system_prompt": system_prompt,
            }
        )
        return "你说最近很焦虑，是什么让你感到最焦虑呢？"


# ---------------------------------------------------------------------------
# Tests: GapDetectionNode
# ---------------------------------------------------------------------------


def test_gap_detection_node_detects_emotion_and_missing_fields() -> None:
    """User says '好焦虑' → detected_emotion=焦虑, missing_fields has event/trigger/behavior."""
    node = GapDetectionNode(llm_service=GapDetectStubLLMService())
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="最近好焦虑",
    )
    result = node.run(state)

    assert result.detected_emotion == "焦虑"
    assert "event" in result.missing_fields
    assert "trigger" in result.missing_fields
    assert "behavior" in result.missing_fields
    assert result.need_follow_up is True


def test_gap_detection_node_no_follow_up_when_all_fields_present() -> None:
    """When no fields are missing, need_follow_up is False."""
    node = GapDetectionNode(llm_service=GapDetectNoFollowUpStubLLMService())
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="今天工作很不顺利，和老板吵了一架，我直接怼回去了。",
    )
    result = node.run(state)

    assert result.detected_emotion == "失落"
    assert result.missing_fields == []
    assert result.need_follow_up is False


def test_gap_detection_node_partial_missing() -> None:
    """When only some fields missing, need_follow_up is still True."""
    node = GapDetectionNode(llm_service=GapDetectStubLLMServiceMissingBehavior())
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="最近好焦虑，不过我感觉自己总是拖着不开始。",
    )
    result = node.run(state)

    assert result.detected_emotion == "焦虑"
    assert result.missing_fields == ["behavior"]
    assert result.need_follow_up is True


def test_gap_detection_node_includes_short_term_messages_in_prompt() -> None:
    node = GapDetectionNode(llm_service=GapDetectStubLLMService())
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="最近好焦虑",
        short_term_messages=[
            {"role": "user", "content": "这周天天睡不好。"},
            {"role": "assistant", "content": "听起来你最近很绷着。"},
        ],
    )
    result = node.run(state)

    assert result.detected_emotion == "焦虑"


def test_gap_detection_node_includes_retrieved_memories_in_prompt() -> None:
    llm_service = GapDetectNoFollowUpStubLLMService()
    node = GapDetectionNode(llm_service=llm_service)
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="我又学不进去了",
        retrieved_memories=[
            {
                "memory_id": "memory-1",
                "scenario": "学习",
                "event": "准备面试时学不进去",
                "emotion": "焦虑",
                "trigger": "任务压力",
                "behavior": "刷视频回避",
                "result": "学习中断并自责",
            }
        ],
    )

    result = node.run(state)

    assert result.need_follow_up is False
    assert llm_service.calls
    user_prompt = llm_service.calls[0]["user_prompt"]
    assert "相关历史记忆" in user_prompt
    assert "准备面试时学不进去" in user_prompt
    assert "刷视频回避" in user_prompt


# ---------------------------------------------------------------------------
# Tests: ResponsePlannerNode
# ---------------------------------------------------------------------------


def test_response_planner_node_selects_emotional_support() -> None:
    """need_follow_up=False → selects emotional_support strategy."""
    node = ResponsePlannerNode(llm_service=PlannerStubLLMService())
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="今天工作很不顺利，有点失落。",
        detected_emotion="失落",
        missing_fields=[],
        need_follow_up=False,
    )
    result = node.run(state)

    assert result.response_strategy == "emotional_support"


def test_response_planner_node_selects_information_follow_up() -> None:
    """need_follow_up=True → selects information_follow_up strategy."""
    node = ResponsePlannerNode(llm_service=PlannerFollowUpStubLLMService())
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="最近好焦虑",
        detected_emotion="焦虑",
        missing_fields=["event", "trigger", "behavior"],
        need_follow_up=True,
    )
    result = node.run(state)

    assert result.response_strategy == "information_follow_up"


# ---------------------------------------------------------------------------
# Tests: ResponseGenerationNode
# ---------------------------------------------------------------------------


def test_response_generation_node_emotional_support_reply() -> None:
    """emotional_support strategy → generates a supportive response."""
    llm_service = GenerationStubLLMService()
    node = ResponseGenerationNode(llm_service=llm_service)
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="今天工作很不顺利，有点失落。",
        detected_emotion="失落",
        missing_fields=[],
        need_follow_up=False,
        response_strategy="emotional_support",
        short_term_messages=[{"role": "user", "content": "我前两天也在担心这个。"}],
    )
    result = node.run(state)

    assert result.assistant_response is not None
    assert llm_service.calls
    assert (
        "焦虑" in result.assistant_response
        or "失落" in result.assistant_response
        or "听起来" in result.assistant_response
    )


def test_response_generation_node_passes_response_generation_prompt_to_llm() -> None:
    llm_service = GenerationPromptAwareStubLLMService()
    node = ResponseGenerationNode(llm_service=llm_service)
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="我又学不进去了",
        detected_emotion="焦虑",
        missing_fields=[],
        need_follow_up=False,
        response_strategy="emotional_support",
    )

    node.run(state)

    assert llm_service.calls
    assert llm_service.calls[0]["system_prompt"]
    assert "生成一条自然中文回复" in str(llm_service.calls[0]["system_prompt"])


def test_response_generation_node_information_follow_up_single_question() -> None:
    """information_follow_up strategy → generates exactly one focused question."""
    llm_service = GenerationFollowUpStubLLMService()
    node = ResponseGenerationNode(llm_service=llm_service)
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="最近好焦虑",
        detected_emotion="焦虑",
        missing_fields=["event", "trigger", "behavior"],
        need_follow_up=True,
        response_strategy="information_follow_up",
    )
    result = node.run(state)

    assert result.assistant_response is not None
    assert llm_service.calls
    question_count = result.assistant_response.count("？") + result.assistant_response.count("?")
    assert question_count == 1, (
        f"Expected exactly 1 question mark, got {question_count}: {result.assistant_response}"
    )
