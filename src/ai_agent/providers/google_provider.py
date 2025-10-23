"""Google Gemini provider implementation."""

from __future__ import annotations

import os
from typing import Iterable, Mapping, MutableMapping, Optional

import requests

from .base import LLMProvider, ProviderError


class GoogleGeminiProvider(LLMProvider):
    """Google Gemini REST API wrapper."""

    def __init__(
        self,
        model: str = "gemini-1.5-pro",
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        super().__init__(name="google")
        self.model = model
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.base_url = base_url or os.getenv(
            "GOOGLE_GEMINI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta",
        )
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable or api_key must be set")

    def generate(
        self,
        messages: Iterable[Mapping[str, str]],
        *,
        temperature: Optional[float] = None,
        extra_params: Optional[MutableMapping[str, object]] = None,
    ) -> str:
        contents = [
            {
                "role": message["role"],
                "parts": [{"text": message["content"]}],
            }
            for message in messages
        ]
        payload: MutableMapping[str, object] = {
            "contents": contents,
        }
        if temperature is not None:
            payload.setdefault("generationConfig", {})["temperature"] = temperature
        if extra_params:
            payload.update(extra_params)

        endpoint = f"{self.base_url}/models/{self.model}:generateContent"
        response = requests.post(
            endpoint,
            params={"key": self.api_key},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        if response.status_code != 200:
            raise ProviderError("google", f"HTTP {response.status_code}", response=response.json())
        data = response.json()
        try:
            return "".join(part.get("text", "") for candidate in data["candidates"] for part in candidate["content"]["parts"])
        except (KeyError, TypeError) as exc:
            raise ProviderError("google", "Unexpected response format", response=data) from exc


__all__ = ["GoogleGeminiProvider"]
