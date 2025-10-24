"""Flask application providing a web interface for Neuro AI."""

from __future__ import annotations

from typing import Any, Dict, List, MutableMapping

from flask import Flask, jsonify, render_template, request

from model.ai_engine import AIEngine, AIEngineError


def create_app() -> Flask:
    """Create and configure the Flask application instance."""

    app = Flask(__name__, template_folder="templates", static_folder="static")

    @app.get("/")
    def index() -> str:
        """Serve the Neuro AI chat interface."""

        return render_template("index.html")

    @app.post("/api/chat")
    def chat() -> Any:
        """Handle chat requests from the frontend."""

        payload: Dict[str, Any] = request.get_json(silent=True) or {}
        message = (payload.get("message") or "").strip()
        history = payload.get("history") or []

        if not message:
            return jsonify({"error": "Please provide a prompt for Neuro AI."}), 400

        conversation: List[MutableMapping[str, str]] = []

        if isinstance(history, list):
            for item in history:
                if not isinstance(item, dict):
                    continue
                role = item.get("role")
                content = item.get("content")
                if isinstance(role, str) and isinstance(content, str):
                    conversation.append({"role": role, "content": content})

        conversation.append({"role": "user", "content": message})

        try:
            with AIEngine() as engine:
                response_text = engine.generate_response(conversation)
        except AIEngineError as error:
            return jsonify({"error": str(error)}), 500

        conversation.append({"role": "assistant", "content": response_text})

        return jsonify({"response": response_text, "history": conversation})

    return app


__all__ = ["create_app"]

