from __future__ import annotations

from uuid import uuid4

from app.models.task import Task


class TaskService:
    def __init__(self, llm_service, task_repo) -> None:
        self.llm_service = llm_service
        self.task_repo = task_repo

    def generate_task(
        self,
        *,
        user_id: str,
        recommended_method: dict,
        llm_adapter=None,
    ) -> Task | None:
        method_id = recommended_method.get("method_id")
        if method_id is None:
            return None
        latest_failed_task = self.task_repo.get_latest_failed_task(user_id, method_id)
        llm = llm_adapter if llm_adapter is not None else self.llm_service
        result = llm.structured_json(
            system_prompt=self._build_system_prompt(),
            user_prompt=self._build_user_prompt(
                recommended_method=recommended_method,
                latest_failed_task=latest_failed_task,
            ),
        )
        difficulty = "adjusted" if latest_failed_task is not None else "low"
        task = Task(
            task_id=str(uuid4()),
            user_id=user_id,
            task_content=result.get("task_content") or self._default_task_content(recommended_method),
            method_id=method_id,
            pattern_id=recommended_method.get("pattern_id"),
            difficulty=difficulty,
            duration_minutes=self._normalize_duration(result.get("duration_minutes")),
            status="pending",
        )
        return self.task_repo.upsert(task)

    def list_tasks(self, *, user_id: str) -> list[Task]:
        return self.task_repo.list_by_user_id(user_id=user_id)

    def update_task_status(self, *, task_id: str, status: str, feedback: str | None = None) -> Task:
        return self.task_repo.update_status(task_id, status=status, feedback=feedback)

    @staticmethod
    def _build_system_prompt() -> str:
        return (
            "你是轻量行动任务生成助手。\n"
            "请输出一个 15-30 分钟内可完成的具体动作。\n"
            "如果用户最近同方法任务失败过，要把任务再缩小一步。\n"
            "输出 JSON，字段仅包含 task_content, duration_minutes, difficulty。"
        )

    @staticmethod
    def _build_user_prompt(*, recommended_method: dict, latest_failed_task: Task | None) -> str:
        failed_text = "无历史失败任务"
        if latest_failed_task is not None:
            failed_text = (
                f"最近失败任务: content={latest_failed_task.task_content}; "
                f"feedback={latest_failed_task.feedback or '无'}"
            )
        return (
            f"method_id={recommended_method.get('method_id')}; "
            f"method_name={recommended_method.get('method_name')}; "
            f"reason={recommended_method.get('reason')}; "
            f"difficulty={recommended_method.get('difficulty')}\n"
            f"pattern_summary={recommended_method.get('pattern_summary')}\n"
            f"{failed_text}"
        )

    @staticmethod
    def _default_task_content(recommended_method: dict) -> str:
        method_name = recommended_method.get("method_name") or "当前方法"
        if recommended_method.get("difficulty") == "adjusted":
            return f"把{method_name}缩成更小的一步，只做 10-15 分钟的最低门槛动作。"
        return f"用 15-30 分钟完成一次{method_name}的最小实践。"

    @staticmethod
    def _normalize_duration(value: object) -> int:
        try:
            duration = int(value)
        except (TypeError, ValueError):
            return 15
        return min(30, max(10, duration))
