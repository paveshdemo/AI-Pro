"""Anthropic Claude provider implementation."""

from __future__ import annotations

import os
from typing import Iterable, Mapping, MutableMapping, Optional

import requests

from .base import LLMProvider, ProviderError


class AnthropicProvider(LLMProvider):
    """Anthropic Claude Messages API wrapper."""

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20240620",
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        super().__init__(name="anthropic")
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url or os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or api_key must be set")

    def generate(
        self,
        messages: Iterable[Mapping[str, str]],
        *,
        temperature: Optional[float] = None,
        extra_params: Optional[MutableMapping[str, object]] = None,
    ) -> str:
        payload: MutableMapping[str, object] = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": list(messages),
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if extra_params:
            payload.update(extra_params)

        response = requests.post(
            f"{self.base_url}/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        if response.status_code != 200:
            raise ProviderError("anthropic", f"HTTP {response.status_code}", response=response.json())
        data = response.json()
        try:
            return "".join(block.get("text", "") for block in data["content"] if block.get("type") == "text")
        except (KeyError, TypeError) as exc:
            raise ProviderError("anthropic", "Unexpected response format", response=data) from exc


__all__ = ["AnthropicProvider"]
