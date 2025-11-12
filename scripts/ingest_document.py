"""CLI helper to ingest lecture PDFs into the Neuro AI document store."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NoReturn

# Ensure the project root is on ``sys.path`` so ``model`` can be imported when the
# script is executed via ``python scripts/ingest_document.py``.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from model.document_store import (  # noqa: E402  - imported after path tweak
    DocumentStore,
    DocumentStoreError,
    EmbeddingClient,
    EmbeddingClientError,
)


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Ingest a lecture PDF so Neuro AI can use it for personalised, context-aware responses."
        )
    )
    parser.add_argument("pdf", type=Path, help="Path to the lecture PDF to ingest.")
    parser.add_argument(
        "--title",
        help="Optional override for the document title stored in the index.",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=None,
        help="Custom path to the document index JSON file (defaults to data/document_index.json).",
    )
    return parser


def ingest(args: argparse.Namespace) -> int:
    """Ingest the requested PDF and return an exit status code."""

    pdf_path = Path(args.pdf).expanduser().resolve()
    index_path = Path(args.index).expanduser().resolve() if args.index else None

    store = DocumentStore(index_path=index_path) if index_path else DocumentStore()

    try:
        with EmbeddingClient() as client:
            meta = store.ingest_pdf(pdf_path, client, title=args.title)
    except (DocumentStoreError, EmbeddingClientError) as error:
        print(f"[error] {error}")
        return 1

    print(
        "[success] Ingested document '{title}' with {count} knowledge sections.".format(
            title=meta.title, count=meta.chunk_count
        )
    )
    return 0


def main(argv: list[str] | None = None) -> NoReturn:
    """Parse arguments and execute the ingestion routine."""

    parser = build_parser()
    args = parser.parse_args(argv)
    exit_code = ingest(args)
    raise SystemExit(exit_code)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
