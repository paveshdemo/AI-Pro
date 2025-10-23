"""Shared abstractions for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Mapping, MutableMapping, Optional


class ProviderError(RuntimeError):
    """Base exception for provider failures."""

    def __init__(self, provider: str, message: str, *, response: Optional[Mapping[str, object]] = None):
        super().__init__(f"{provider} provider error: {message}")
        self.provider = provider
        self.message = message
        self.response = dict(response or {})


class LLMProvider(ABC):
    """Abstract base class implemented by concrete LLM providers."""

    name: str

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate(
        self,
        messages: Iterable[Mapping[str, str]],
        *,
        temperature: Optional[float] = None,
        extra_params: Optional[MutableMapping[str, object]] = None,
    ) -> str:
        """Generate text from the provider."""


__all__ = ["LLMProvider", "ProviderError"]
