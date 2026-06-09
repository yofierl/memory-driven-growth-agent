from __future__ import annotations

from datetime import UTC, datetime

from pymongo.collection import Collection

from app.models.conversation import Conversation


class ConversationRepository:
    def __init__(self, collection: Collection) -> None:
        self.collection = collection

    def get_by_conversation_id(self, conversation_id: str) -> Conversation | None:
        document = self.collection.find_one({"conversation_id": conversation_id})
        if document is None:
            return None
        document.pop("_id", None)
        return Conversation.model_validate(document)

    def save(self, conversation: Conversation) -> Conversation:
        payload = conversation.model_dump(mode="python")
        payload["updated_at"] = datetime.now(UTC)
        self.collection.update_one(
            {"conversation_id": conversation.conversation_id},
            {
                "$set": {k: v for k, v in payload.items() if k != "created_at"},
                "$setOnInsert": {"created_at": payload["created_at"]},
            },
            upsert=True,
        )
        stored = self.get_by_conversation_id(conversation.conversation_id)
        return stored or conversation
