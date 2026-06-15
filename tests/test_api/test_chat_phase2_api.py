from fastapi.testclient import TestClient

from app.main import create_app


class Phase2LLMService:
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
        if user_message == "最近好焦虑":
            return "你说最近很焦虑，是什么让你感到最焦虑呢？"
        return "听起来这件事让你不太好受，可以继续说说。"

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        self.structured_json_calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
            }
        )
        if "risk_detection" in system_prompt:
            return {"risk_level": "none", "risk_reason": "test ordinary input"}
        if (
            "gap_detection" in system_prompt
            or "missing_fields" in system_prompt
            or "detected_emotion" in system_prompt
        ):
            return {
                "detected_emotion": "焦虑",
                "missing_fields": ["event", "trigger", "behavior"],
            }
        if "response_planner" in system_prompt or "response_strategy" in system_prompt:
            return {"response_strategy": "information_follow_up"}
        if "new_memories" in system_prompt:
            return {
                "new_memories": [
                    {
                        "type": "emotion_event",
                        "scenario": "近期生活",
                        "event": "近期感到焦虑",
                        "emotion": "焦虑",
                        "importance": 4,
                        "confidence": 0.82,
                        "source": "conversation",
                    }
                ]
            }
        raise AssertionError(f"Unexpected system prompt: {system_prompt[:80]}")


class InMemoryUserRepo:
    def __init__(self) -> None:
        self.users: dict[str, object] = {}

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


def build_test_client() -> TestClient:
    app = create_app()
    app.dependency_overrides = {}
    app.state.test_llm_service = Phase2LLMService()
    app.state.test_user_repo = InMemoryUserRepo()
    app.state.test_conversation_repo = InMemoryConversationRepo()
    app.state.test_memory_repo = InMemoryMemoryRepo()
    return TestClient(app)


def test_chat_phase2_uses_langgraph_follow_up_workflow() -> None:
    client = build_test_client()

    response = client.post(
        "/api/chat",
        json={"user_id": "user-1", "message": "最近好焦虑"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["strategy"] == "information_follow_up"
    assert payload["assistant_response"]
    llm_service = client.app.state.test_llm_service
    assert len(llm_service.generate_reply_calls) == 1
    generation_call = llm_service.generate_reply_calls[0]
    assert generation_call["conversation_messages"] == []
    assert "回复策略：information_follow_up" in generation_call["user_message"]
    assert payload["retrieved_memories"] == []
    assert payload["detected_patterns"] == []
    assert payload["generated_task"] is None


def test_chat_phase2_persists_conversation_via_real_chat_endpoint() -> None:
    client = build_test_client()

    first_response = client.post(
        "/api/chat",
        json={"user_id": "user-1", "message": "最近好焦虑"},
    )
    assert first_response.status_code == 200
    conversation_id = first_response.json()["conversation_id"]

    second_response = client.post(
        "/api/chat",
        json={
            "user_id": "user-1",
            "conversation_id": conversation_id,
            "message": "是工作压力太大。",
        },
    )

    assert second_response.status_code == 200
    assert second_response.json()["conversation_id"] == conversation_id


def test_chat_phase2_reuses_graph_instance_on_app_state() -> None:
    client = build_test_client()

    first_response = client.post(
        "/api/chat",
        json={"user_id": "user-1", "message": "最近好焦虑"},
    )
    assert first_response.status_code == 200
    first_graph = client.app.state.growth_agent_graph

    second_response = client.post(
        "/api/chat",
        json={"user_id": "user-1", "message": "最近好焦虑"},
    )
    assert second_response.status_code == 200
    assert client.app.state.growth_agent_graph is first_graph


def test_chat_phase2_passes_short_term_messages_to_gap_detection() -> None:
    client = build_test_client()

    first_response = client.post(
        "/api/chat",
        json={"user_id": "user-1", "message": "这周天天睡不好。"},
    )
    assert first_response.status_code == 200
    conversation_id = first_response.json()["conversation_id"]

    second_response = client.post(
        "/api/chat",
        json={
            "user_id": "user-1",
            "conversation_id": conversation_id,
            "message": "最近好焦虑",
        },
    )
    assert second_response.status_code == 200

    llm_service = client.app.state.test_llm_service
    gap_prompt = llm_service.structured_json_calls[-3]["user_prompt"]
    assert "这周天天睡不好" in gap_prompt
