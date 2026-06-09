from datetime import UTC, datetime

from app.models.conversation import Conversation, ConversationMessage
from app.models.memory import Memory
from app.models.user import User


def test_phase1_models_can_be_instantiated() -> None:
    user = User(user_id="user-1", nickname="Codex")
    conversation = Conversation(
        conversation_id="conv-1",
        user_id="user-1",
        messages=[ConversationMessage(role="user", content="我今天学不进去")],
    )
    memory = Memory(
        memory_id="memory-1",
        user_id="user-1",
        type="emotion_event",
        scenario="学习",
        event="学不进去",
        emotion="焦虑",
        trigger="任务压力大",
        behavior="刷视频回避",
        result="学习中断",
        source="conversation",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert user.user_id == "user-1"
    assert conversation.messages[0].role == "user"
    assert memory.type == "emotion_event"
    assert memory.behavior == "刷视频回避"
