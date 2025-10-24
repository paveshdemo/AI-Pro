"""Controller logic for the ChatGPT-style chatbot.

The controller orchestrates the interaction between the view and the model. It
collects user input, forwards conversation history to the AI engine, and renders
responses. It also centralizes error handling so that any issues are reported in
an informative manner to the user.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, MutableMapping

from model.ai_engine import AIEngine, AIEngineError
from view.console_ui import ConsoleUI


@dataclass(slots=True)
class ChatController:
    """Connects the model (:class:`AIEngine`) with the view (:class:`ConsoleUI`)."""

    view: ConsoleUI
    model: AIEngine
    conversation_history: List[MutableMapping[str, str]] = field(default_factory=list)

    def run(self) -> None:
        """Start the chatbot conversation loop until the user types ``"exit"``."""

        self.view.display_welcome()

        while True:
            user_input = self.view.request_user_input().strip()
            if not user_input:
                continue  # Ignore empty submissions to keep the conversation pleasant.

            if user_input.lower() == "exit":
                self.view.display_goodbye()
                break

            self._record_user_message(user_input)

            try:
                response = self.model.generate_response(self.conversation_history)
            except AIEngineError as error:
                self.view.display_error(str(error))
                # Remove the most recent user message so that a retry does not
                # duplicate the same prompt in history.
                self.conversation_history.pop()
                continue

            self._record_bot_message(response)
            self.view.display_bot_response(response)

    # Internal helpers -------------------------------------------------------------
    def _record_user_message(self, message: str) -> None:
        """Append a user message to the conversation history."""

        self.conversation_history.append({"role": "user", "content": message})

    def _record_bot_message(self, message: str) -> None:
        """Append a chatbot response to the conversation history."""

        self.conversation_history.append({"role": "assistant", "content": message})
