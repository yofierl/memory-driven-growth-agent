from fastapi.testclient import TestClient

from app.main import create_app


class InMemoryLLMService:
    def generate_reply(self, *, user_message: str, conversation_messages: list[dict]) -> str:
        assert user_message == "我今天又学不进去。"
        return "听起来你现在有点被压力卡住了，我们先把这件事说具体一点。"

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        assert "new_memories" in system_prompt
        assert "我今天又学不进去。" in user_prompt
        return {
            "new_memories": [
                {
                    "type": "emotion_event",
                    "scenario": "学习",
                    "event": "今天学不进去",
                    "emotion": "焦虑",
                    "trigger": "任务太多",
                    "behavior": "拖着不开始",
                    "result": "晚上自责",
                    "importance": 4,
                    "confidence": 0.88,
                    "source": "conversation",
                }
            ]
        }


class InMemoryUserRepo:
    def __init__(self) -> None:
        self.users: dict[str, dict] = {}

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


class InMemoryMemoryRepo:
    def __init__(self) -> None:
        self.memories: list[object] = []

    def create_many(self, memories):
        self.memories.extend(memories)
        return memories

    def list_by_user_id(self, user_id: str, memory_type=None):
        items = [memory for memory in self.memories if memory.user_id == user_id]
        if memory_type:
            items = [memory for memory in items if memory.type == memory_type]
        return items


def build_test_client() -> TestClient:
    app = create_app()
    app.dependency_overrides = {}
    app.state.test_llm_service = InMemoryLLMService()
    app.state.test_user_repo = InMemoryUserRepo()
    app.state.test_conversation_repo = InMemoryConversationRepo()
    app.state.test_memory_repo = InMemoryMemoryRepo()
    return TestClient(app)


def test_chat_simple_creates_memory_and_returns_reply() -> None:
    client = build_test_client()

    response = client.post(
        "/api/chat/simple",
        json={"user_id": "user-1", "message": "我今天又学不进去。"},
    )

    assert response.status_code == 200
    payload = response.json()
    expected_reply = "听起来你现在有点被压力卡住了，我们先把这件事说具体一点。"
    assert payload["assistant_response"] == expected_reply
    assert payload["strategy"] == "simple_chat"
    assert payload["stored_memory_count"] == 1
    assert payload["memories"][0]["event"] == "今天学不进去"
    assert payload["memories"][0]["emotion"] == "焦虑"
    assert payload["memories"][0]["trigger"] == "任务太多"
    assert payload["memories"][0]["behavior"] == "拖着不开始"
    assert payload["memories"][0]["result"] == "晚上自责"


def test_list_memories_returns_phase1_stored_memories() -> None:
    client = build_test_client()
    create_response = client.post(
        "/api/chat/simple",
        json={"user_id": "user-1", "message": "我今天又学不进去。"},
    )
    assert create_response.status_code == 200

    response = client.get("/api/memories", params={"user_id": "user-1"})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["memories"]) == 1
    assert payload["memories"][0]["type"] == "emotion_event"
    assert payload["memories"][0]["event"] == "今天学不进去"
