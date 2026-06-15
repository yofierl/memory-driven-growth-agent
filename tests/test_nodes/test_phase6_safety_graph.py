from app.agent.graph import GrowthAgentGraph
from app.agent.state import GrowthAgentState
from app.models.memory import Memory


class Phase6LLMStub:
    def __init__(self, risk_level: str) -> None:
        self.risk_level = risk_level
        self.structured_calls: list[dict[str, str]] = []
        self.generate_calls: list[dict[str, object]] = []

    def generate_reply(
        self,
        *,
        system_prompt: str | None = None,
        user_message: str,
        conversation_messages: list[dict],
    ) -> str:
        self.generate_calls.append(
            {
                "system_prompt": system_prompt,
                "user_message": user_message,
                "conversation_messages": conversation_messages,
            }
        )
        return "I can stay with this and help you make the next step smaller."

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        self.structured_calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
        if "risk_detection" in system_prompt:
            return {
                "risk_level": self.risk_level,
                "risk_reason": "test risk classification",
            }
        if "gap_detection" in system_prompt or "missing_fields" in system_prompt:
            return {"detected_emotion": "anxiety", "missing_fields": []}
        if "response_planner" in system_prompt:
            return {"response_strategy": "emotional_support"}
        if "new_memories" in system_prompt:
            return {"new_memories": []}
        return {}


class RecordingSafetyLogRepo:
    def __init__(self) -> None:
        self.logs: list[object] = []

    def insert(self, safety_log):
        self.logs.append(safety_log)
        return safety_log


class Phase6MemoryServiceStub:
    def __init__(self) -> None:
        self.search_calls: list[dict[str, object]] = []
        self.add_calls: list[Memory] = []

    def search_memories(
        self,
        query: str,
        filters: dict | None = None,
        top_k: int = 3,
    ):
        self.search_calls.append({"query": query, "filters": filters, "top_k": top_k})
        return []

    def add_memory(self, memory: Memory) -> Memory:
        self.add_calls.append(memory)
        return memory

    def list_memories(self, user_id: str, filters: dict | None = None):
        return []


def test_growth_agent_graph_routes_high_risk_to_safety_and_stops_normal_flow() -> None:
    llm_service = Phase6LLMStub(risk_level="high")
    memory_service = Phase6MemoryServiceStub()
    safety_log_repo = RecordingSafetyLogRepo()
    graph = GrowthAgentGraph(
        llm_service=llm_service,
        memory_service=memory_service,
        safety_log_repo=safety_log_repo,
    )

    result = graph.run(
        GrowthAgentState(
            user_id="user-1",
            conversation_id="conv-1",
            user_input="I might hurt myself tonight.",
        )
    )

    assert result.risk_level == "high"
    assert result.safety_handled is True
    assert "immediate danger" in (result.assistant_response or "")
    assert memory_service.search_calls == []
    assert memory_service.add_calls == []
    assert result.retrieved_memories == []
    assert result.new_memories == []
    assert result.detected_patterns == []
    assert result.generated_task is None
    assert len(safety_log_repo.logs) == 1
    assert safety_log_repo.logs[0].risk_level == "high"
    assert not hasattr(safety_log_repo.logs[0], "user_input")


def test_growth_agent_graph_continues_existing_flow_for_none_risk() -> None:
    llm_service = Phase6LLMStub(risk_level="none")
    memory_service = Phase6MemoryServiceStub()
    graph = GrowthAgentGraph(llm_service=llm_service, memory_service=memory_service)

    result = graph.run(
        GrowthAgentState(
            user_id="user-1",
            conversation_id="conv-1",
            user_input="I keep procrastinating when a task feels too big.",
        )
    )

    assert result.risk_level == "none"
    assert result.safety_handled is False
    assert memory_service.search_calls
    assert result.response_strategy == "emotional_support"
    assert result.assistant_response


def test_keyword_l1_does_not_bypass_llm_when_llm_downgrades_risk() -> None:
    llm_service = Phase6LLMStub(risk_level="none")
    memory_service = Phase6MemoryServiceStub()
    graph = GrowthAgentGraph(llm_service=llm_service, memory_service=memory_service)

    result = graph.run(
        GrowthAgentState(
            user_id="user-1",
            conversation_id="conv-1",
            user_input="I wrote about suicide prevention resources for class.",
        )
    )

    assert result.risk_level == "none"
    assert result.safety_handled is False
    assert memory_service.search_calls
    assert llm_service.structured_calls[0]["system_prompt"].startswith("risk_detection")
    assert "L1" in llm_service.structured_calls[0]["user_prompt"]


def test_keyword_l2_injects_prior_signal_without_forcing_high_risk() -> None:
    llm_service = Phase6LLMStub(risk_level="none")
    memory_service = Phase6MemoryServiceStub()
    graph = GrowthAgentGraph(llm_service=llm_service, memory_service=memory_service)

    result = graph.run(
        GrowthAgentState(
            user_id="user-1",
            conversation_id="conv-1",
            user_input="今晚就开始复习，不再拖了。",
        )
    )

    assert result.risk_level == "none"
    assert result.safety_handled is False
    assert memory_service.search_calls
    assert "L2" in llm_service.structured_calls[0]["user_prompt"]
