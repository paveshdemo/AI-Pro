"""OpenAI provider implementation using the chat completions REST API."""

from __future__ import annotations

import os
from typing import Iterable, Mapping, MutableMapping, Optional

import requests

from .base import LLMProvider, ProviderError


class OpenAIProvider(LLMProvider):
    """OpenAI Chat Completions API wrapper."""

    def __init__(self, model: str = "gpt-4o-mini", *, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(name="openai")
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable or api_key must be set")

    def generate(
        self,
        messages: Iterable[Mapping[str, str]],
        *,
        temperature: Optional[float] = None,
        extra_params: Optional[MutableMapping[str, object]] = None,
    ) -> str:
        payload: MutableMapping[str, object] = {
            "model": self.model,
            "messages": list(messages),
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if extra_params:
            payload.update(extra_params)

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        if response.status_code != 200:
            raise ProviderError("openai", f"HTTP {response.status_code}", response=response.json())
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ProviderError("openai", "Unexpected response format", response=data) from exc


__all__ = ["OpenAIProvider"]
