"""Bulk-ingest personal project documents for Neuro AI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List

# Make sure ``model`` can be imported when the script is executed directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from model.document_store import (  # noqa: E402  - imported after path tweak
    DocumentStore,
    DocumentStoreError,
    EmbeddingClient,
    EmbeddingClientError,
)


def iter_pdf_files(root: Path) -> Iterable[Path]:
    """Yield all PDF files within ``root`` (recursively)."""

    root = root.expanduser().resolve()

    if not root.exists():
        return []
    if root.is_file():
        return [root] if root.suffix.lower() == ".pdf" else []

    pdfs: List[Path] = []
    for path in sorted(root.rglob("*.pdf")):
        if path.is_file():
            pdfs.append(path)
    return pdfs


def ingest_directory(directory: Path) -> int:
    """Ingest every PDF in ``directory`` and return an exit status code."""

    target_directory = Path(directory).expanduser().resolve()
    pdfs = list(iter_pdf_files(target_directory))
    if not pdfs:
        print(f"[info] No PDF files found in {target_directory}.")
        return 0

    try:
        store = DocumentStore()
    except DocumentStoreError as error:
        print(f"[error] Failed to initialise document store: {error}")
        return 1

    successes = 0
    failures = 0

    try:
        with EmbeddingClient() as client:
            for pdf_path in pdfs:
                try:
                    meta = store.ingest_pdf(pdf_path, client)
                except DocumentStoreError as error:
                    print(f"[error] Could not ingest '{pdf_path.name}': {error}")
                    failures += 1
                else:
                    print(
                        "[success] Ingested '{title}' from {path} with {count} sections.".format(
                            title=meta.title,
                            path=pdf_path,
                            count=meta.chunk_count,
                        )
                    )
                    successes += 1
    except EmbeddingClientError as error:
        print(f"[error] Failed to generate embeddings: {error}")
        return 1

    print(
        "[summary] Completed ingestion: {successes} succeeded, {failures} failed.".format(
            successes=successes,
            failures=failures,
        )
    )

    return 0 if failures == 0 else 2


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Ingest every PDF stored in your custom project files directory so Neuro AI "
            "can reference them during chats."
        )
    )
    parser.add_argument(
        "directory",
        type=Path,
        nargs="?",
        default=Path(__file__).resolve().parent.parent / "project_files",
        help=(
            "Path to the folder containing your personal PDF documents. Defaults to the "
            "'project_files' directory in the project root."
        ),
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    """Entry point for command-line execution."""

    parser = build_parser()
    args = parser.parse_args(argv)
    return ingest_directory(args.directory)


if __name__ == "__main__":  # pragma: no cover - CLI helper
    raise SystemExit(main())
