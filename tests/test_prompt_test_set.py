import json
from pathlib import Path


def test_prompt_test_set_has_30_labeled_items_covering_mvp_categories() -> None:
    path = Path("data/prompt_tests/mvp_prompt_test_set.jsonl")

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    categories = {row["category"] for row in rows}

    assert len(rows) == 30
    assert {
        "anxiety",
        "procrastination",
        "high_sensitivity",
        "rumination",
        "confusion",
        "small_talk",
        "high_risk",
    }.issubset(categories)
    assert all("input" in row and row["input"] for row in rows)
    assert all("expected" in row and isinstance(row["expected"], dict) for row in rows)
