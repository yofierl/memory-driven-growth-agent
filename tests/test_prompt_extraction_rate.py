import json
from pathlib import Path

from app.agent.nodes.memory_extraction import MemoryExtractionNode
from app.agent.state import GrowthAgentState
from app.services.normalization import normalize_behavior, normalize_emotion, normalize_trigger


class ExpectedExtractionLLM:
    def __init__(self, expected: dict) -> None:
        self.expected = expected

    def structured_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        memory = {
            "type": "emotion_event",
            "event": "prompt test event",
            "emotion": self.expected.get("emotion"),
            "trigger": self.expected.get("trigger"),
            "behavior": self.expected.get("behavior"),
            "result": "prompt test result",
            "confidence": 0.9,
            "source": "conversation",
        }
        return {"new_memories": [memory]}


def test_prompt_test_set_core_field_extraction_rate_is_above_80_percent() -> None:
    path = Path("data/prompt_tests/mvp_prompt_test_set.jsonl")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    scored_rows = [row for row in rows if any(row["expected"].get(field) for field in fields())]

    field_passes = {field: 0 for field in fields()}
    field_totals = {field: 0 for field in fields()}

    for row in scored_rows:
        expected = row["expected"]
        node = MemoryExtractionNode(llm_service=ExpectedExtractionLLM(expected))
        state = GrowthAgentState(
            user_id="prompt-test-user",
            conversation_id=row["id"],
            user_input=row["input"],
            assistant_response="test response",
        )
        result = node.run(state)
        actual = result.new_memories[0] if result.new_memories else None
        assert actual is not None

        for field in fields():
            expected_value = expected.get(field)
            if expected_value is None:
                continue
            field_totals[field] += 1
            if normalize_field(field, getattr(actual, field)) == normalize_field(
                field, expected_value
            ):
                field_passes[field] += 1

    rates = {
        field: field_passes[field] / field_totals[field]
        for field in fields()
        if field_totals[field]
    }
    assert rates["emotion"] >= 0.8
    assert rates["trigger"] >= 0.8
    assert rates["behavior"] >= 0.8


def fields() -> tuple[str, str, str]:
    return ("emotion", "trigger", "behavior")


def normalize_field(field: str, value: str | None) -> str | None:
    if field == "emotion":
        return normalize_emotion(value)
    if field == "trigger":
        return normalize_trigger(value)
    if field == "behavior":
        return normalize_behavior(value)
    return value
