"""Utilities for building providers from environment configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from .providers.anthropic_provider import AnthropicProvider
from .providers.base import LLMProvider
from .providers.google_provider import GoogleGeminiProvider
from .providers.openai_provider import OpenAIProvider


DEFAULT_ENV_FILENAMES: Sequence[str] = ("keys.env", ".env")


def _load_env_file(path: Path) -> None:
    """Load environment variables from a simple ``KEY=VALUE`` file."""

    try:
        data = path.read_text(encoding="utf-8")
    except OSError:
        return

    for raw_line in data.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith("\"") and value.endswith("\"")) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        os.environ[key] = value


def load_environment_from_files(filenames: Sequence[str] = DEFAULT_ENV_FILENAMES) -> None:
    """Load environment variables from the provided filenames if present."""

    seen: set[Path] = set()
    search_roots = {Path.cwd(), *Path(__file__).resolve().parents}
    for root in search_roots:
        for name in filenames:
            candidate = (root / name).resolve()
            if candidate in seen or not candidate.is_file():
                continue
            seen.add(candidate)
            _load_env_file(candidate)


def build_default_providers() -> List[LLMProvider]:
    """Build provider instances for any API keys found in the environment."""

    load_environment_from_files()

    providers: List[LLMProvider] = []
    if os.getenv("OPENAI_API_KEY"):
        providers.append(OpenAIProvider())
    if os.getenv("ANTHROPIC_API_KEY"):
        providers.append(AnthropicProvider())
    if os.getenv("GOOGLE_API_KEY"):
        providers.append(GoogleGeminiProvider())
    if not providers:
        raise RuntimeError(
            "No providers configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY."
        )
    return providers


def parse_provider_selection(selection: Optional[str], *, available: Iterable[str]) -> str:
    """Validate the provider selection from CLI or user input."""

    if not selection:
        return next(iter(available))
    selection = selection.lower()
    names: Dict[str, str] = {name.lower(): name for name in available}
    if selection not in names:
        raise KeyError(f"Provider '{selection}' is not available. Choices: {', '.join(sorted(available))}")
    return names[selection]


__all__ = [
    "build_default_providers",
    "load_environment_from_files",
    "parse_provider_selection",
]
