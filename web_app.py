"""Flask application providing a web interface for Neuro AI."""

from __future__ import annotations

from typing import Any, Dict, List, MutableMapping

from flask import Flask, jsonify, render_template, request

from model.ai_engine import AIEngine, AIEngineError
from model.document_store import (
    DocumentStore,
    DocumentStoreError,
    EmbeddingClient,
    EmbeddingClientError,
)


def create_app() -> Flask:
    """Create and configure the Flask application instance."""

    app = Flask(__name__, template_folder="templates", static_folder="static")

    try:
        document_store = DocumentStore()
    except DocumentStoreError as error:  # pragma: no cover - start-up scenario
        app.logger.warning("Failed to load lecture document index: %s", error)
        document_store = None

    app.config["DOCUMENT_STORE"] = document_store

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

        contextual_messages: List[MutableMapping[str, str]] = []
        store = app.config.get("DOCUMENT_STORE")
        if store and store.has_content():
            try:
                with EmbeddingClient() as embedder:
                    search_results = store.search(message, embedder)
            except EmbeddingClientError as error:  # pragma: no cover - runtime scenario
                app.logger.warning("Failed to retrieve lecture context: %s", error)
            else:
                if search_results:
                    top_chunks = [chunk for _score, chunk in search_results]
                    contextual_messages.append(
                        {
                            "role": "system",
                            "content": store.build_system_prompt(top_chunks),
                        }
                    )

        try:
            with AIEngine() as engine:
                response_text = engine.generate_response(contextual_messages + conversation)
        except AIEngineError as error:
            return jsonify({"error": str(error)}), 500

        conversation.append({"role": "assistant", "content": response_text})

        return jsonify({"response": response_text, "history": conversation})

    return app


__all__ = ["create_app"]

