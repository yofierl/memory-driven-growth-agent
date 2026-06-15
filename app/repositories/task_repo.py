from __future__ import annotations

from datetime import UTC, datetime

from pymongo.collection import Collection

from app.core.exceptions import TaskNotFoundError
from app.models.task import Task


class TaskRepository:
    def __init__(self, collection: Collection) -> None:
        self.collection = collection

    def list_by_user_id(self, user_id: str, statuses: list[str] | None = None) -> list[Task]:
        query: dict[str, object] = {"user_id": user_id}
        if statuses:
            query["status"] = {"$in": statuses}
        cursor = self.collection.find(query).sort("created_at", -1)
        return [self._to_model(document) for document in cursor]

    def get_by_task_id(self, task_id: str) -> Task | None:
        document = self.collection.find_one({"task_id": task_id})
        return self._to_model(document) if document else None

    def get_latest_failed_task(self, user_id: str, method_id: str) -> Task | None:
        document = self.collection.find_one(
            {"user_id": user_id, "method_id": method_id, "status": "failed"},
            sort=[("updated_at", -1)],
        )
        return self._to_model(document) if document else None

    def upsert(self, task: Task) -> Task:
        payload = task.model_dump(mode="python")
        payload["updated_at"] = datetime.now(UTC)
        self.collection.update_one(
            {"task_id": task.task_id},
            {
                "$set": {k: v for k, v in payload.items() if k != "created_at"},
                "$setOnInsert": {"created_at": payload["created_at"]},
            },
            upsert=True,
        )
        stored = self.get_by_task_id(task.task_id)
        return stored or task

    def update_status(self, task_id: str, *, status: str, feedback: str | None = None) -> Task:
        update_fields: dict[str, object] = {
            "status": status,
            "updated_at": datetime.now(UTC),
        }
        if feedback is not None:
            update_fields["feedback"] = feedback
        result = self.collection.find_one_and_update(
            {"task_id": task_id},
            {"$set": update_fields},
            return_document=True,
        )
        if result is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")
        return self._to_model(result)

    @staticmethod
    def _to_model(document: dict | None) -> Task:
        assert document is not None
        document.pop("_id", None)
        return Task.model_validate(document)
