from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.schemas.memory_schema import MemoryResponse
from app.schemas.pattern_schema import PatternResponse
from app.schemas.task_schema import TaskResponse


def test_core_response_schemas_can_be_instantiated() -> None:
    chat_request = ChatRequest(user_id="user-1", conversation_id="conv-1", message="hello")
    chat_response = ChatResponse(
        conversation_id="conv-1",
        assistant_response="hello",
        strategy="emotional_support",
    )
    memory_response = MemoryResponse(
        memory_id="memory-1",
        user_id="user-1",
        type="emotion_event",
    )
    pattern_response = PatternResponse(
        pattern_id="pattern-1",
        user_id="user-1",
        status="detected",
        evidence_memory_ids=["memory-1", "memory-2", "memory-3"],
    )
    task_response = TaskResponse(
        task_id="task-1",
        user_id="user-1",
        task_content="Do one small thing.",
        status="pending",
    )

    assert chat_request.user_id == "user-1"
    assert chat_response.conversation_id == "conv-1"
    assert memory_response.memory_id == "memory-1"
    assert pattern_response.evidence_memory_ids == ["memory-1", "memory-2", "memory-3"]
    assert task_response.status == "pending"
