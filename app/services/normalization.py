from __future__ import annotations

EMOTION_SYNONYMS: dict[str, set[str]] = {
    "焦虑": {"焦虑", "慌", "压力很大", "很焦虑", "紧张"},
}

TRIGGER_SYNONYMS: dict[str, set[str]] = {
    "任务压力": {"任务压力", "任务压力太大", "任务太多", "任务过大"},
}

BEHAVIOR_SYNONYMS: dict[str, set[str]] = {
    "刷视频回避": {"刷视频", "看短视频", "刷B站", "刷抖音", "刷视频回避"},
    "拖延回避": {"不想开始", "拖着", "学不进去", "拖延", "拖延回避"},
}


def normalize_emotion(raw: str | None) -> str | None:
    return _normalize(raw, EMOTION_SYNONYMS)


def normalize_trigger(raw: str | None) -> str | None:
    return _normalize(raw, TRIGGER_SYNONYMS)


def normalize_behavior(raw: str | None) -> str | None:
    return _normalize(raw, BEHAVIOR_SYNONYMS)


def _normalize(raw: str | None, synonyms: dict[str, set[str]]) -> str | None:
    if raw is None:
        return None
    value = str(raw).strip()
    if not value:
        return None
    compact = "".join(value.lower().split())
    for canonical, variants in synonyms.items():
        for variant in variants:
            normalized_variant = "".join(variant.lower().split())
            if compact == normalized_variant or normalized_variant in compact:
                return canonical
    return value
