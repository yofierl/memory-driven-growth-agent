from __future__ import annotations

from collections import defaultdict
from uuid import uuid4

from app.models.memory import Memory
from app.models.pattern import Pattern


class PatternService:
    def __init__(self, pattern_repo) -> None:
        self.pattern_repo = pattern_repo

    def discover_patterns(
        self,
        *,
        user_id: str,
        memories: list[Memory],
        llm_service,
    ) -> list[Pattern]:
        grouped_memories = self._group_candidate_memories(memories)
        discovered_patterns: list[Pattern] = []

        for grouped in grouped_memories:
            evidence_memory_ids = [memory.memory_id for memory in grouped]
            if len(set(evidence_memory_ids)) < 3:
                continue

            sample = grouped[0]
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(grouped)
            result = llm_service.structured_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            for item in result.get("patterns", []):
                pattern = self._build_pattern(
                    user_id=user_id,
                    sample=sample,
                    grouped_memories=grouped,
                    payload=item,
                )
                if pattern is None:
                    continue
                existing = self.pattern_repo.get_detected_by_signature(
                    user_id=user_id,
                    scenario=pattern.scenario,
                    trigger=pattern.trigger,
                    emotion=pattern.emotion,
                    behavior=pattern.behavior,
                )
                if existing is not None and existing.status == "rejected":
                    continue
                updated_pattern = pattern
                if existing is not None:
                    update_dict: dict[str, object] = {
                        **pattern.model_dump(),
                        "pattern_id": existing.pattern_id,
                    }
                    if existing.status in ("confirmed", "detected"):
                        update_dict["status"] = existing.status
                    updated_pattern = existing.model_copy(update=update_dict)
                stored = self.pattern_repo.upsert(updated_pattern)
                discovered_patterns.append(stored)

        return discovered_patterns

    @staticmethod
    def _group_candidate_memories(memories: list[Memory]) -> list[list[Memory]]:
        buckets: dict[tuple[str | None, str, str, str], list[Memory]] = defaultdict(list)
        for memory in memories:
            if memory.type != "emotion_event":
                continue
            if not memory.trigger or not memory.emotion or not memory.behavior:
                continue
            key = (
                PatternService._normalize(memory.scenario),
                PatternService._normalize(memory.trigger),
                PatternService._normalize(memory.emotion),
                PatternService._normalize(memory.behavior),
            )
            buckets[key].append(memory)
        return [group for group in buckets.values() if len({item.memory_id for item in group}) >= 3]

    @staticmethod
    def _build_system_prompt() -> str:
        return (
            "你是行为模式发现助手。\n"
            "输入是一组已经按 scenario/emotion/trigger/behavior 聚合过的 emotion_event 记忆。\n"
            "仅在这些记忆明显构成重复链路时输出 patterns。\n"
            "每个 pattern 只总结 trigger/emotion/behavior/result/scenario/confidence。\n"
            '如果证据不足或不稳定，返回 {"patterns": []}。'
        )

    @staticmethod
    def _build_user_prompt(memories: list[Memory]) -> str:
        lines = []
        for memory in memories:
            lines.append(
                f"memory_id={memory.memory_id}; scenario={memory.scenario or '无'}; "
                f"event={memory.event or '无'}; emotion={memory.emotion or '无'}; "
                f"trigger={memory.trigger or '无'}; behavior={memory.behavior or '无'}; "
                f"result={memory.result or '无'}"
            )
        return "候选证据记忆：\n" + "\n".join(lines)

    @staticmethod
    def _build_pattern(
        *,
        user_id: str,
        sample: Memory,
        grouped_memories: list[Memory],
        payload: dict,
    ) -> Pattern | None:
        evidence_memory_ids = []
        seen = set()
        for memory in grouped_memories:
            if memory.memory_id in seen:
                continue
            seen.add(memory.memory_id)
            evidence_memory_ids.append(memory.memory_id)
        if len(evidence_memory_ids) < 3:
            return None

        result_text = payload.get("result") or sample.result
        trigger = payload.get("trigger") or sample.trigger
        emotion = payload.get("emotion") or sample.emotion
        behavior = payload.get("behavior") or sample.behavior
        if not trigger or not emotion or not behavior or not result_text:
            return None

        confidence = payload.get("confidence", 0.0)
        try:
            confidence_value = float(confidence)
        except (TypeError, ValueError):
            confidence_value = 0.0
        confidence_value = max(0.0, min(1.0, confidence_value))

        return Pattern(
            pattern_id=str(uuid4()),
            user_id=user_id,
            scenario=payload.get("scenario") or sample.scenario,
            trigger=str(trigger),
            emotion=str(emotion),
            behavior=str(behavior),
            result=str(result_text),
            frequency=len(evidence_memory_ids),
            evidence_memory_ids=evidence_memory_ids,
            confidence=confidence_value,
            status="detected",
        )

    @staticmethod
    def _normalize(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None
