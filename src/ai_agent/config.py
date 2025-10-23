"""Utilities for building providers from environment configuration."""

from __future__ import annotations

import os
from typing import Dict, Iterable, List, Optional

from .providers.anthropic_provider import AnthropicProvider
from .providers.google_provider import GoogleGeminiProvider
from .providers.openai_provider import OpenAIProvider
from .providers.base import LLMProvider


def build_default_providers() -> List[LLMProvider]:
    """Build provider instances for any API keys found in the environment."""

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


__all__ = ["build_default_providers", "parse_provider_selection"]
