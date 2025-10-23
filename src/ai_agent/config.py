"""Utilities for building providers from environment configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Sequence

from .providers.base import LLMProvider
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
        if not root.exists():
            continue
        for name in filenames:
            if root.is_file():
                candidates: Iterable[Path] = []
            else:
                candidates = root.rglob(name)
            for candidate in candidates:
                candidate = candidate.resolve()
                if candidate in seen or not candidate.is_file():
                    continue
                seen.add(candidate)
                _load_env_file(candidate)


def build_default_providers() -> List[LLMProvider]:
    """Build provider instances for any API keys found in the environment."""

    load_environment_from_files()

    try:
        provider = OpenAIProvider()
    except ValueError as exc:
        raise RuntimeError(
            "No providers configured. Set the OPENAI_API_KEY environment variable or add it to keys.env."
        ) from exc
    return [provider]


__all__ = [
    "build_default_providers",
    "load_environment_from_files",
]
