from pathlib import Path
from typing import Any

from jinja2 import Template

from app.core.config import get_settings
from app.core.exceptions import PromptNotFoundError


class PromptLoader:
    def __init__(self, prompt_dir: Path | None = None, cache_enabled: bool = True) -> None:
        self.prompt_dir = prompt_dir or get_settings().prompt_dir
        self.cache_enabled = cache_enabled
        self._cache: dict[str, str] = {}

    def load(self, name: str) -> str:
        prompt_name = name if name.endswith(".md") else f"{name}.md"
        if self.cache_enabled and prompt_name in self._cache:
            return self._cache[prompt_name]

        prompt_path = self.prompt_dir / prompt_name
        try:
            content = prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise PromptNotFoundError(
                f"Prompt file not found: {prompt_path} (resolved from prompt_dir={self.prompt_dir})"
            ) from None
        if self.cache_enabled:
            self._cache[prompt_name] = content
        return content

    def render(self, name: str, variables: dict[str, Any] | None = None) -> str:
        template = Template(self.load(name))
        return template.render(**(variables or {}))


prompt_loader = PromptLoader()
