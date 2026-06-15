from fastapi.testclient import TestClient

from app.main import create_app
from app.models.task import Task


class InMemoryTaskRepo:
    def __init__(self) -> None:
        self.tasks: dict[str, Task] = {}

    def list_by_user_id(self, user_id: str, statuses: list[str] | None = None):
        results = [task for task in self.tasks.values() if task.user_id == user_id]
        if statuses is not None:
            results = [task for task in results if task.status in statuses]
        return sorted(results, key=lambda item: item.created_at, reverse=True)

    def get_by_task_id(self, task_id: str):
        return self.tasks.get(task_id)

    def upsert(self, task: Task):
        self.tasks[task.task_id] = task
        return task

    def update_status(self, task_id: str, *, status: str, feedback: str | None = None):
        task = self.tasks[task_id]
        updated = task.model_copy(update={"status": status, "feedback": feedback})
        self.tasks[task_id] = updated
        return updated


def build_task(*, task_id: str, status: str = "pending", feedback: str | None = None) -> Task:
    return Task(
        task_id=task_id,
        user_id="user-1",
        task_content="用 15 分钟把待办拆成第一步，并只启动一次。",
        method_id="method-15min-start",
        status=status,
        feedback=feedback,
    )


def test_list_tasks_returns_user_tasks() -> None:
    app = create_app()
    repo = InMemoryTaskRepo()
    repo.upsert(build_task(task_id="task-1"))
    repo.upsert(build_task(task_id="task-2", status="failed", feedback="难度太高"))
    app.state.test_task_repo = repo
    client = TestClient(app)

    response = client.get("/api/tasks", params={"user_id": "user-1"})

    assert response.status_code == 200
    payload = response.json()
    assert [item["task_id"] for item in payload["tasks"]] == ["task-2", "task-1"]
    assert payload["tasks"][0]["status"] == "failed"
    assert payload["tasks"][0]["feedback"] == "难度太高"


def test_update_task_status_records_feedback() -> None:
    app = create_app()
    repo = InMemoryTaskRepo()
    repo.upsert(build_task(task_id="task-1"))
    app.state.test_task_repo = repo
    client = TestClient(app)

    response = client.post(
        "/api/tasks/task-1/status",
        params={"user_id": "user-1"},
        json={"status": "failed", "feedback": "这次还是太难开始了"},
    )

    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert repo.get_by_task_id("task-1").status == "failed"
    assert repo.get_by_task_id("task-1").feedback == "这次还是太难开始了"


def test_update_task_status_returns_404_for_missing_task() -> None:
    app = create_app()
    app.state.test_task_repo = InMemoryTaskRepo()
    client = TestClient(app)

    response = client.post(
        "/api/tasks/missing/status",
        params={"user_id": "user-1"},
        json={"status": "completed"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "task_not_found"
