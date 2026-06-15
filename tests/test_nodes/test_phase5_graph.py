from app.agent.graph import GrowthAgentGraph
from app.agent.state import GrowthAgentState
from app.models.memory import Memory
from app.models.pattern import Pattern
from app.models.task import Task


class Phase5GraphLLMStub:
    def generate_reply(
        self,
        *,
        system_prompt: str | None = None,
        user_message: str,
        conversation_messages: list[dict],
    ):
        return "收到，我会先陪你把眼前这一步变小。"

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        if "missing_fields" in system_prompt or "gap_detection" in system_prompt:
            return {"detected_emotion": "焦虑", "missing_fields": []}
        if "response_planner" in system_prompt:
            return {"response_strategy": "emotional_support"}
        if "new_memories" in system_prompt:
            return {"new_memories": []}
        if "patterns" in system_prompt:
            return {"patterns": []}
        if (
            "intervention_routing" in system_prompt
            or "method_id=" in user_prompt
            and "patterns" not in system_prompt
            and "patterns" not in user_prompt
            and "missing_fields" not in system_prompt
        ):
            return {
                "method_id": "method_15_min_start",
                "method_name": "15 分钟启动法",
                "reason": "当前模式表现为面对任务压力时拖延，先降低启动门槛更合适。",
                "difficulty": "low",
            }
        if "task_generation" in system_prompt:
            return {
                "task_content": "现在只做 15 分钟，把任务拆成第一步并启动计时。",
                "duration_minutes": 15,
                "difficulty": "low",
            }
        return {}


class Phase5GraphMemoryServiceStub:
    def __init__(self) -> None:
        self.list_calls: list[dict[str, object]] = []

    def search_memories(self, query: str, filters: dict | None = None, top_k: int = 3):
        return []

    def add_memory(self, memory: Memory) -> Memory:
        return memory

    def list_memories(self, user_id: str, filters: dict | None = None):
        self.list_calls.append({"user_id": user_id, "filters": filters})
        return []


class Phase5PatternRepoStub:
    def __init__(self, confirmed_patterns: list[Pattern] | None = None) -> None:
        self.confirmed_patterns = confirmed_patterns or []

    def list_by_user_id(self, user_id: str, statuses: list[str] | None = None):
        if statuses == ["confirmed"]:
            return self.confirmed_patterns
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


class Phase5TaskRepoStub:
    def __init__(self) -> None:
        self.saved_tasks: list[Task] = []
        self.latest_failed: Task | None = None

    def upsert(self, task: Task):
        self.saved_tasks.append(task)
        return task

    def get_latest_failed_task(self, user_id: str, method_id: str):
        if (
            self.latest_failed is not None
            and self.latest_failed.user_id == user_id
            and self.latest_failed.method_id == method_id
        ):
            return self.latest_failed
        return None


class Phase5MethodRepoStub:
    def list_all(self):
        return [
            {
                "method_id": "method_15_min_start",
                "name": "15 分钟启动法",
                "description": "把任务压缩到一个容易启动的 15 分钟动作。",
                "target_problem": ["拖延", "回避", "任务压力过大"],
                "steps": ["选择一个最小任务", "设置 15 分钟", "只要求开始", "结束后记录感受"],
                "difficulty": "low",
            }
        ]


def make_confirmed_pattern() -> Pattern:
    return Pattern(
        pattern_id="pattern-1",
        user_id="user-1",
        scenario="学习",
        trigger="任务压力",
        emotion="焦虑",
        behavior="刷视频回避",
        result="进度中断",
        frequency=3,
        evidence_memory_ids=["m1", "m2", "m3"],
        confidence=0.82,
        status="confirmed",
    )


def test_growth_agent_graph_routes_confirmed_patterns_to_intervention_and_task_generation() -> None:
    task_repo = Phase5TaskRepoStub()
    graph = GrowthAgentGraph(
        llm_service=Phase5GraphLLMStub(),
        memory_service=Phase5GraphMemoryServiceStub(),
        pattern_repo=Phase5PatternRepoStub([make_confirmed_pattern()]),
        method_repo=Phase5MethodRepoStub(),
        task_repo=task_repo,
    )

    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="我这周又因为任务压力开始逃避。",
    )
    result = graph.run(state)

    assert result.pattern_confirmation_required is False
    assert result.recommended_method is not None
    assert result.recommended_method["method_id"] == "method_15_min_start"
    assert result.generated_task is not None
    assert result.generated_task["method_id"] == "method_15_min_start"
    assert result.generated_task["status"] == "pending"
    assert result.generated_task["difficulty"] == "low"
    assert "15" in result.generated_task["task_content"]
    assert len(task_repo.saved_tasks) == 1


def test_growth_agent_graph_skips_intervention_when_no_confirmed_patterns() -> None:
    task_repo = Phase5TaskRepoStub()
    graph = GrowthAgentGraph(
        llm_service=Phase5GraphLLMStub(),
        memory_service=Phase5GraphMemoryServiceStub(),
        pattern_repo=Phase5PatternRepoStub([]),
        method_repo=Phase5MethodRepoStub(),
        task_repo=task_repo,
    )

    state = GrowthAgentState(
        user_id="user-1",
        conversation_id="conv-1",
        user_input="我这周又因为任务压力开始逃避。",
    )
    result = graph.run(state)

    assert result.recommended_method is None
    assert result.generated_task is None
    assert task_repo.saved_tasks == []
