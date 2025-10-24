"""Entry point for the ChatGPT-like console chatbot project.

This module wires together the MVC components—model, view, and controller—and
starts the interactive chat loop when executed as a script.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from controller.chat_controller import ChatController
from model.ai_engine import AIEngine
from view.console_ui import ConsoleUI


def load_environment_from_file(filename: str = "keys.env") -> None:
    """Load environment variables from a simple ``KEY=VALUE`` file if present.

    The project relies on ``OPENAI_API_KEY`` being available as an environment
    variable. For convenience, this helper reads a ``keys.env`` file residing in
    the project root and populates the variables without requiring an additional
    dependency such as :mod:`python-dotenv`.
    """

    env_path = Path(filename)
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def supports_color() -> bool:
    """Determine whether ANSI color codes should be used for output."""

    if os.getenv("NO_COLOR") is not None:
        return False
    return sys.stdout.isatty()


def main() -> None:
    """Run the ChatGPT-like chatbot using the MVC components."""

    load_environment_from_file()

    console_ui = ConsoleUI(enable_color=supports_color())

    with AIEngine() as engine:
        controller = ChatController(view=console_ui, model=engine)
        controller.run()


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
