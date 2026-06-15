from __future__ import annotations

from app.models.method import Method
from app.models.pattern import Pattern


class InterventionService:
    def __init__(self, pattern_repo, method_repo, task_repo) -> None:
        self.pattern_repo = pattern_repo
        self.method_repo = method_repo
        self.task_repo = task_repo

    def route_method(self, *, user_id: str, llm_service) -> dict | None:
        confirmed_patterns = self.pattern_repo.list_by_user_id(
            user_id=user_id, statuses=["confirmed"]
        )
        if not confirmed_patterns:
            return None
        methods = [
            Method.model_validate(m) if not isinstance(m, Method) else m
            for m in self.method_repo.list_all()
        ]
        if not methods:
            return None

        latest_pattern = confirmed_patterns[0]
        method_lookup = {method.method_id: method for method in methods}
        fallback_method = self._fallback_method(latest_pattern=latest_pattern, methods=methods)
        latest_failed_task = self.task_repo.get_latest_failed_task(
            user_id, fallback_method.method_id
        )

        result = llm_service.structured_json(
            system_prompt=self._build_system_prompt(),
            user_prompt=self._build_user_prompt(
                pattern=latest_pattern,
                methods=methods,
                latest_failed_task=latest_failed_task,
            ),
        )
        selected_method = method_lookup.get(result.get("method_id"), fallback_method)
        difficulty = "adjusted" if latest_failed_task is not None else "low"
        requested_difficulty = result.get("difficulty")
        if requested_difficulty in {"low", "adjusted"}:
            difficulty = "adjusted" if latest_failed_task is not None else requested_difficulty

        return {
            "method_id": selected_method.method_id,
            "method_name": result.get("method_name") or selected_method.name,
            "reason": result.get("reason") or self._default_reason(selected_method),
            "difficulty": difficulty,
            "pattern_id": latest_pattern.pattern_id,
            "pattern_summary": {
                "trigger": latest_pattern.trigger,
                "emotion": latest_pattern.emotion,
                "behavior": latest_pattern.behavior,
                "result": latest_pattern.result,
            },
        }

    @staticmethod
    def _build_system_prompt() -> str:
        return "请选择一个最适合当前 confirmed pattern 的方法。"

    @staticmethod
    def _build_user_prompt(
        *,
        pattern: Pattern,
        methods: list[Method],
        latest_failed_task,
    ) -> str:
        method_lines = []
        for method in methods:
            method_lines.append(
                f"method_id={method.method_id}; name={method.name}; "
                f"target_problem={'/'.join(method.target_problem)}; "
                f"difficulty={method.difficulty}; steps={' | '.join(method.steps)}"
            )
        failed_text = "无"
        if latest_failed_task is not None:
            failed_text = (
                f"最近失败任务: task_id={latest_failed_task.task_id}; "
                f"content={latest_failed_task.task_content}; "
                f"feedback={latest_failed_task.feedback or '无'}"
            )
        return (
            f"confirmed pattern: trigger={pattern.trigger}; emotion={pattern.emotion}; "
            f"behavior={pattern.behavior}; result={pattern.result}\n"
            f"{failed_text}\n"
            "methods:\n" + "\n".join(method_lines)
        )

    @staticmethod
    def _fallback_method(*, latest_pattern: Pattern, methods: list[Method]) -> Method:
        emotion = latest_pattern.emotion
        behavior = latest_pattern.behavior
        result = latest_pattern.result
        if any(value in (None, "无") for value in (emotion, behavior, result)):
            return methods[0]
        for method in methods:
            tags = " ".join(method.target_problem)
            if any(keyword in tags for keyword in (behavior, emotion, result)):
                return method
        return methods[0]

    @staticmethod
    def _default_reason(method: Method) -> str:
        return f"先用{method.name}把行动门槛降到足够小。"
