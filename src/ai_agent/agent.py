"""Core agent logic for orchestrating conversations across multiple LLM providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from .providers.base import LLMProvider, ProviderError


@dataclass
class ChatMessage:
    """Represents a single chat message."""

    role: str
    content: str


@dataclass
class ConversationState:
    """Simple in-memory conversation state container."""

    messages: List[ChatMessage] = field(default_factory=list)

    def append(self, message: ChatMessage) -> None:
        self.messages.append(message)

    def as_dict(self) -> List[Dict[str, str]]:
        return [message.__dict__ for message in self.messages]


class MultiModelChatAgent:
    """Coordinator that can route chat requests to different providers."""

    def __init__(self, providers: Iterable[LLMProvider], default_provider: Optional[str] = None):
        self._providers: Dict[str, LLMProvider] = {provider.name: provider for provider in providers}
        if not self._providers:
            raise ValueError("At least one provider must be configured")
        if default_provider is None:
            default_provider = next(iter(self._providers))
        if default_provider not in self._providers:
            raise KeyError(f"Unknown default provider '{default_provider}'")
        self._default_provider = default_provider
        self._conversations: Dict[str, ConversationState] = {}

    @property
    def providers(self) -> Dict[str, LLMProvider]:
        return dict(self._providers)

    @property
    def default_provider(self) -> str:
        return self._default_provider

    def set_default_provider(self, provider_name: str) -> None:
        if provider_name not in self._providers:
            raise KeyError(f"Provider '{provider_name}' is not registered")
        self._default_provider = provider_name

    def chat(
        self,
        prompt: str,
        *,
        provider_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Send a prompt to the selected provider and return the response."""

        if provider_name is None:
            provider_name = self._default_provider
        provider = self._providers.get(provider_name)
        if provider is None:
            raise KeyError(f"Provider '{provider_name}' is not registered")

        state = self._conversations.setdefault(conversation_id or provider_name, ConversationState())
        state.append(ChatMessage(role="user", content=prompt))

        try:
            response = provider.generate(state.as_dict(), temperature=temperature)
        except ProviderError:
            # propagate provider-specific errors to the caller with context
            raise

        state.append(ChatMessage(role="assistant", content=response))
        return response

    def reset_conversation(self, conversation_id: Optional[str] = None) -> None:
        """Clear the conversation memory for the provided conversation id."""

        if conversation_id is None:
            self._conversations.clear()
        else:
            self._conversations.pop(conversation_id, None)


__all__ = ["MultiModelChatAgent", "ChatMessage"]
