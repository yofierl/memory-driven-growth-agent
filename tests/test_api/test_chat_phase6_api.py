from fastapi.testclient import TestClient

from app.main import create_app
from app.models.conversation import Conversation
from app.models.memory import Memory
from app.models.method import Method
from app.models.pattern import Pattern
from app.models.task import Task
from app.models.user import User


class Phase6ChatLLMService:
    def generate_reply(
        self,
        *,
        system_prompt: str | None = None,
        user_message: str,
        conversation_messages: list[dict],
    ) -> str:
        return "I hear the pattern. Let us make the next step small and concrete."

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        if "risk_detection" in system_prompt:
            if "hurt myself" in user_prompt:
                return {"risk_level": "high", "risk_reason": "explicit self-harm"}
            return {"risk_level": "none", "risk_reason": "ordinary growth input"}
        if "gap_detection" in system_prompt or "missing_fields" in system_prompt:
            return {"detected_emotion": "anxiety", "missing_fields": []}
        if "response_planner" in system_prompt:
            return {"response_strategy": "emotional_support"}
        if "new_memories" in system_prompt:
            return {
                "new_memories": [
                    {
                        "type": "emotion_event",
                        "scenario": "study",
                        "event": "avoided a demanding task",
                        "emotion": "anxiety",
                        "trigger": "task pressure",
                        "behavior": "procrastination",
                        "result": "progress stopped",
                        "confidence": 0.9,
                    }
                ]
            }
        if "patterns" in system_prompt:
            return {"patterns": []}
        if "intervention_routing" in system_prompt:
            return {
                "method_id": "method_15_min_start",
                "method_name": "15 minute start",
                "reason": "task pressure leads to avoidance",
                "difficulty": "low",
            }
        if "task_generation" in system_prompt:
            return {
                "task_content": "Start one study task for 15 minutes.",
                "duration_minutes": 15,
                "difficulty": "low",
            }
        return {}


class Phase6UserRepo:
    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    def get_by_user_id(self, user_id: str):
        return self.users.get(user_id)

    def upsert(self, user: User):
        self.users[user.user_id] = user
        return user


class Phase6ConversationRepo:
    def __init__(self) -> None:
        self.conversations: dict[str, Conversation] = {}

    def get_by_conversation_id(self, conversation_id: str):
        return self.conversations.get(conversation_id)

    def save(self, conversation: Conversation):
        self.conversations[conversation.conversation_id] = conversation
        return conversation


class Phase6MemoryService:
    def __init__(self) -> None:
        self.added: list[Memory] = []
        self.search_calls: list[str] = []

    def search_memories(self, query: str, filters: dict | None = None, top_k: int = 3):
        self.search_calls.append(query)
        return []

    def add_memory(self, memory: Memory) -> Memory:
        self.added.append(memory)
        return memory

    def list_memories(self, user_id: str, filters: dict | None = None):
        return []


class Phase6PatternRepo:
    def list_by_user_id(self, user_id: str, statuses: list[str] | None = None):
        if statuses == ["confirmed"]:
            return [
                Pattern(
                    pattern_id="pattern-1",
                    user_id=user_id,
                    scenario="study",
                    trigger="task pressure",
                    emotion="anxiety",
                    behavior="procrastination",
                    result="progress stopped",
                    frequency=3,
                    evidence_memory_ids=["m1", "m2", "m3"],
                    confidence=0.9,
                    status="confirmed",
                )
            ]
        return []

    def get_detected_by_signature(
        self,
        *,
        user_id: str,
        scenario: str | None,
        trigger: str,
        emotion: str,
        behavior: str,
    ):
        return None

    def upsert(self, pattern: Pattern):
        return pattern


class Phase6MethodRepo:
    def list_all(self):
        return [
            Method(
                method_id="method_15_min_start",
                name="15 minute start",
                description="Make the first action small enough to begin.",
                target_problem=["procrastination", "task pressure"],
                steps=["choose one task", "set a 15 minute timer", "start only"],
                difficulty="low",
            )
        ]


class Phase6TaskRepo:
    def __init__(self) -> None:
        self.saved: list[Task] = []

    def upsert(self, task: Task):
        self.saved.append(task)
        return task

    def get_latest_failed_task(self, user_id: str, method_id: str):
        return None


def build_phase6_client():
    app = create_app()
    memory_service = Phase6MemoryService()
    task_repo = Phase6TaskRepo()
    app.state.test_llm_service = Phase6ChatLLMService()
    app.state.test_user_repo = Phase6UserRepo()
    app.state.test_conversation_repo = Phase6ConversationRepo()
    app.state.test_memory_service = memory_service
    app.state.test_pattern_repo = Phase6PatternRepo()
    app.state.test_method_repo = Phase6MethodRepo()
    app.state.test_task_repo = task_repo
    return TestClient(app), memory_service, task_repo


def test_formal_chat_api_runs_three_demo_inputs_through_complete_mvp_loop() -> None:
    client, memory_service, task_repo = build_phase6_client()
    demo_inputs = [
        "I wanted to study, but I watched short videos for two hours instead.",
        "The assignment feels too big, so I keep cleaning my desk instead of starting.",
        "I delayed the resume project again because I did not know the first step.",
    ]

    for message in demo_inputs:
        response = client.post(
            "/api/chat",
            json={"user_id": "demo-user", "message": message},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["risk_level"] == "none"
        assert payload["safety_handled"] is False
        assert payload["generated_task"]["method_id"] == "method_15_min_start"

    assert len(memory_service.added) == 3
    assert len(task_repo.saved) == 3


def test_formal_chat_api_routes_high_risk_input_to_safety_response() -> None:
    client, memory_service, task_repo = build_phase6_client()

    response = client.post(
        "/api/chat",
        json={"user_id": "demo-user", "message": "I might hurt myself tonight."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["strategy"] == "safety_response"
    assert payload["risk_level"] == "high"
    assert payload["safety_handled"] is True
    assert "immediate danger" in payload["assistant_response"]
    assert memory_service.search_calls == []
    assert memory_service.added == []
    assert task_repo.saved == []
