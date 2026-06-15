from fastapi.testclient import TestClient

from app.main import create_app
from app.models.memory import Memory
from app.models.user import User


class InMemoryUserRepo:
    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    def get_by_user_id(self, user_id: str):
        return self.users.get(user_id)

    def upsert(self, user):
        self.users[user.user_id] = user
        return user


class InMemoryConversationRepo:
    def __init__(self) -> None:
        self.conversations: dict[str, object] = {}

    def get_by_conversation_id(self, conversation_id: str):
        return self.conversations.get(conversation_id)

    def save(self, conversation):
        self.conversations[conversation.conversation_id] = conversation
        return conversation


class Phase3LLMService:
    def __init__(self) -> None:
        self.generate_reply_calls: list[dict[str, object]] = []
        self.structured_json_calls: list[dict[str, str]] = []

    def generate_reply(
        self,
        *,
        user_message: str,
        conversation_messages: list[dict],
        system_prompt: str | None = None,
    ) -> str:
        self.generate_reply_calls.append(
            {
                "user_message": user_message,
                "conversation_messages": conversation_messages,
                "system_prompt": system_prompt,
            }
        )
        assert "准备面试时学不进去" in user_message
        assert "刷视频回避" in user_message
        return "你之前也提到过，任务压力会让你焦虑并刷视频回避。"

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        self.structured_json_calls.append(
            {"system_prompt": system_prompt, "user_prompt": user_prompt}
        )
        if "risk_detection" in system_prompt:
            return {"risk_level": "none", "risk_reason": "test ordinary input"}
        if "gap_detection" in system_prompt or "missing_fields" in system_prompt:
            return {"detected_emotion": "焦虑", "missing_fields": []}
        if "response_planner" in system_prompt or "response_strategy" in system_prompt:
            return {"response_strategy": "emotional_support"}
        if "new_memories" in system_prompt:
            return {
                "new_memories": [
                    {
                        "type": "emotion_event",
                        "scenario": "学习",
                        "event": "再次提到学不进去",
                        "emotion": "焦虑",
                        "trigger": "任务压力",
                        "behavior": "拖延",
                        "result": "进度中断",
                        "confidence": 0.8,
                    }
                ]
            }
        raise AssertionError(f"Unexpected system prompt: {system_prompt[:80]}")


class Phase3MemoryService:
    def __init__(self) -> None:
        self.added_memories: list[Memory] = []

    def search_memories(self, query: str, filters: dict | None = None, top_k: int = 3):
        return [
            Memory(
                memory_id="memory-history",
                user_id="user-1",
                type="emotion_event",
                scenario="学习",
                event="准备面试时学不进去",
                emotion="焦虑",
                trigger="任务压力",
                behavior="刷视频回避",
                result="学习中断并自责",
                confidence=0.92,
            )
        ]

    def add_memory(self, memory: Memory) -> Memory:
        self.added_memories.append(memory)
        return memory


def test_chat_phase3_uses_retrieved_memory_and_memory_update_node() -> None:
    app = create_app()
    app.state.test_llm_service = Phase3LLMService()
    app.state.test_user_repo = InMemoryUserRepo()
    app.state.test_conversation_repo = InMemoryConversationRepo()
    app.state.test_memory_service = Phase3MemoryService()
    client = TestClient(app)

    response = client.post(
        "/api/chat",
        json={"user_id": "user-1", "message": "我又学不进去了"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["retrieved_memories"][0]["memory_id"] == "memory-history"
    assert "刷视频回避" in payload["assistant_response"]
    assert app.state.test_memory_service.added_memories
