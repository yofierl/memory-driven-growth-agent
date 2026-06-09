from app.agent.nodes.memory_extraction import MemoryExtractionNode
from app.agent.state import GrowthAgentState
from app.models.memory import Memory


class StubLLMService:
    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        assert "new_memories" in system_prompt
        assert "学不进去" in user_prompt
        return {
            "new_memories": [
                {
                    "type": "emotion_event",
                    "scenario": "学习",
                    "event": "今天学不进去",
                    "emotion": "焦虑",
                    "trigger": "任务太多",
                    "behavior": "刷视频回避",
                    "result": "晚上自责",
                    "importance": 4,
                    "confidence": 0.91,
                    "source": "conversation",
                }
            ]
        }


class LowConfidenceStubLLMService:
    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        assert "new_memories" in system_prompt
        assert "学不进去" in user_prompt
        return {
            "new_memories": [
                {
                    "type": "emotion_event",
                    "scenario": "学习",
                    "event": "今天学不进去",
                    "emotion": "焦虑",
                    "trigger": "任务太多",
                    "behavior": "刷视频回避",
                    "result": "晚上自责",
                    "importance": 4,
                    "confidence": 0.42,
                    "source": "conversation",
                }
            ]
        }


def test_memory_extraction_node_ignores_low_confidence_memories() -> None:
    node = MemoryExtractionNode(llm_service=LowConfidenceStubLLMService())
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="我今天又学不进去，刷了一下午视频，晚上很自责。",
        assistant_response="听起来你今天被任务压力拖住了。",
    )

    result = node.run(state)

    assert result.new_memories == []


def test_memory_extraction_node_returns_structured_memories() -> None:
    node = MemoryExtractionNode(llm_service=StubLLMService())
    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="我今天又学不进去，刷了一下午视频，晚上很自责。",
        assistant_response="听起来你今天被任务压力拖住了。",
    )

    result = node.run(state)

    assert len(result.new_memories) == 1
    memory = result.new_memories[0]
    assert isinstance(memory, Memory)
    assert memory.event == "今天学不进去"
    assert memory.emotion == "焦虑"
    assert memory.trigger == "任务太多"
    assert memory.behavior == "刷视频回避"
    assert memory.result == "晚上自责"
