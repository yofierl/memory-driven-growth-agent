from app.core.prompt_loader import PromptLoader


def test_prompt_loader_renders_jinja_variables(tmp_path) -> None:
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (prompt_dir / "greeting.md").write_text("Hello {{ name }}.", encoding="utf-8")
    loader = PromptLoader(prompt_dir=prompt_dir, cache_enabled=False)

    rendered = loader.render("greeting", {"name": "Codex"})

    assert rendered == "Hello Codex."
