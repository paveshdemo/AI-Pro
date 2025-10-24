"""Entry point for the Neuro AI web application."""

from __future__ import annotations

import os
from pathlib import Path

from web_app import create_app


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


def main() -> None:
    """Run the Neuro AI Flask development server."""

    load_environment_from_file()

    app = create_app()
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
