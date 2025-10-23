"""Command line interface for interacting with the multi-model chat agent."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

if __package__ in (None, ""):
    import pathlib

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ai_agent.agent import MultiModelChatAgent
from ai_agent.config import build_default_providers, parse_provider_selection


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Chat with multiple AI providers using one tool.")
    parser.add_argument("prompt", nargs="?", help="Prompt to send. If omitted, read from stdin.")
    parser.add_argument("--provider", help="Provider to use (openai, anthropic, google).")
    parser.add_argument("--temperature", type=float, default=None, help="Sampling temperature for the model.")
    parser.add_argument("--json", action="store_true", help="Return raw JSON output instead of plain text.")
    parser.add_argument("--conversation", help="Conversation id to maintain state across requests.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    prompt = args.prompt or sys.stdin.read().strip()
    if not prompt:
        parser.error("Prompt is required either as an argument or via stdin")

    providers = build_default_providers()
    agent = MultiModelChatAgent(providers)

    try:
        provider_name = parse_provider_selection(args.provider, available=agent.providers.keys())
    except ValueError as exc:
        parser.error(str(exc))

    agent.set_default_provider(provider_name)

    response = agent.chat(
        prompt,
        conversation_id=args.conversation,
        temperature=args.temperature,
    )

    if args.json:
        payload = {
            "provider": provider_name,
            "response": response,
        }
        print(json.dumps(payload))
    else:
        print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
