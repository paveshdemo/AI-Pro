"""Console-based user interface for the ChatGPT-style chatbot.

This module implements the View component in the MVC architecture. It is
responsible for interacting with the user via the terminal, displaying prompts,
responses, and helpful status messages. The UI intentionally remains simple so
that the focus stays on the MVC flow and OpenAI integration.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final


class AnsiColor:
    """Collection of ANSI escape sequences used for colorful terminal output."""

    RESET: Final[str] = "\033[0m"
    USER: Final[str] = "\033[96m"  # Bright cyan
    BOT: Final[str] = "\033[92m"  # Bright green
    ERROR: Final[str] = "\033[91m"  # Bright red
    INFO: Final[str] = "\033[94m"  # Bright blue


@dataclass(slots=True)
class ConsoleUI:
    """Lightweight console UI for interacting with the chatbot."""

    enable_color: bool = True

    def _colorize(self, text: str, color: str) -> str:
        """Wrap ``text`` in the provided ANSI ``color`` code if enabled."""

        if not self.enable_color:
            return text
        return f"{color}{text}{AnsiColor.RESET}"

    # User prompts -----------------------------------------------------------------
    def display_welcome(self) -> None:
        """Print a welcome banner to the console."""

        print(self._colorize("Welcome to the ChatGPT-like console chatbot!", AnsiColor.INFO))
        print(self._colorize("Type your questions below. Type 'exit' to end the conversation.", AnsiColor.INFO))

    def request_user_input(self) -> str:
        """Prompt the user for input and return their response."""

        prompt = self._colorize("You: ", AnsiColor.USER)
        return input(prompt)

    # Chatbot responses ------------------------------------------------------------
    def display_bot_response(self, message: str) -> None:
        """Display the chatbot's response to the user."""

        header = self._colorize("Chatbot:", AnsiColor.BOT)
        print(f"{header} {message}")

    def display_error(self, error_message: str) -> None:
        """Display an error message in a user-friendly format."""

        header = self._colorize("Error:", AnsiColor.ERROR)
        print(f"{header} {error_message}")

    def display_goodbye(self) -> None:
        """Say goodbye when the user ends the chat."""

        print(self._colorize("Goodbye! Thanks for chatting.", AnsiColor.INFO))
