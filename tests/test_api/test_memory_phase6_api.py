from fastapi.testclient import TestClient

from app.main import create_app
from app.models.memory import Memory


class Phase6MemoryService:
    def __init__(self) -> None:
        self.memories: dict[str, Memory] = {
            "memory-1": Memory(
                memory_id="memory-1",
                user_id="user-1",
                type="emotion_event",
                scenario="study",
                event="could not start a task",
                emotion="anxiety",
                trigger="task pressure",
                behavior="watched videos",
                result="lost the evening",
                confidence=0.9,
            )
        }
        self.updated: list[dict[str, object]] = []
        self.deleted: list[str] = []

    def list_memories(self, user_id: str, filters: dict | None = None):
        return [
            memory
            for memory in self.memories.values()
            if memory.user_id == user_id and not memory.is_deleted
        ]

    def get_by_id(self, memory_id: str):
        memory = self.memories.get(memory_id)
        if memory is None or memory.is_deleted:
            return None
        return memory

    def update_memory(self, memory_id: str, patch: dict) -> Memory:
        self.updated.append({"memory_id": memory_id, "patch": patch})
        if memory_id not in self.memories:
            raise KeyError(memory_id)
        updated = self.memories[memory_id].model_copy(update=patch)
        self.memories[memory_id] = updated
        return updated

    def delete_memory(self, memory_id: str) -> bool:
        self.deleted.append(memory_id)
        if memory_id not in self.memories:
            return False
        self.memories[memory_id] = self.memories[memory_id].model_copy(update={"is_deleted": True})
        return True


def build_client() -> tuple[TestClient, Phase6MemoryService]:
    app = create_app()
    service = Phase6MemoryService()
    app.state.test_memory_service = service
    app.state.test_memory_repo = service
    return TestClient(app), service


def test_update_memory_api_uses_memory_service() -> None:
    client, service = build_client()

    response = client.patch(
        "/api/memories/memory-1",
        params={"user_id": "user-1"},
        json={"behavior": "started with a smaller task", "confidence": 0.95},
    )

    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert service.updated == [
        {
            "memory_id": "memory-1",
            "patch": {
                "behavior": "started with a smaller task",
                "confidence": 0.95,
            },
        }
    ]
    assert service.memories["memory-1"].behavior == "started with a smaller task"


def test_delete_memory_api_uses_memory_service() -> None:
    client, service = build_client()

    response = client.delete("/api/memories/memory-1", params={"user_id": "user-1"})

    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert service.deleted == ["memory-1"]
    assert service.memories["memory-1"].is_deleted is True


def test_memory_mutation_api_returns_404_for_missing_memory() -> None:
    client, _ = build_client()

    update_response = client.patch(
        "/api/memories/missing",
        params={"user_id": "user-1"},
        json={"behavior": "changed"},
    )
    delete_response = client.delete("/api/memories/missing", params={"user_id": "user-1"})

    assert update_response.status_code == 404
    assert update_response.json()["error"]["code"] == "memory_not_found"
    assert delete_response.status_code == 404
    assert delete_response.json()["error"]["code"] == "memory_not_found"


def test_memory_mutation_api_rejects_cross_user_patch() -> None:
    client, service = build_client()

    response = client.patch(
        "/api/memories/memory-1",
        params={"user_id": "user-2"},
        json={"behavior": "cross-user edit"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "memory_not_found"
    assert service.updated == []
