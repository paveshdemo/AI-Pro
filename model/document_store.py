"""Utilities for ingesting and retrieving lecture documents for context-aware chats."""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, MutableMapping, Optional, Sequence, Tuple
from uuid import uuid4

import requests
from pypdf import PdfReader


class DocumentStoreError(RuntimeError):
    """Raised when ingesting or searching the document store fails."""


class EmbeddingClientError(RuntimeError):
    """Raised when requesting embeddings from the OpenAI API fails."""


@dataclass(slots=True)
class DocumentMeta:
    """Metadata describing an ingested document."""

    document_id: str
    title: str
    source_path: str | None
    chunk_count: int


@dataclass(slots=True)
class DocumentChunk:
    """Represents a chunk of a document along with its embedding."""

    chunk_id: str
    document_id: str
    document_title: str
    index: int
    text: str
    embedding: List[float]

    def to_dict(self) -> MutableMapping[str, object]:
        """Convert the chunk to a JSON-serialisable mapping."""

        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "document_title": self.document_title,
            "index": self.index,
            "text": self.text,
            "embedding": self.embedding,
        }

    @classmethod
    def from_dict(cls, payload: MutableMapping[str, object]) -> "DocumentChunk":
        """Restore a :class:`DocumentChunk` from a JSON mapping."""

        return cls(
            chunk_id=str(payload.get("chunk_id")),
            document_id=str(payload.get("document_id")),
            document_title=str(payload.get("document_title")),
            index=int(payload.get("index", 0)),
            text=str(payload.get("text", "")),
            embedding=[float(value) for value in payload.get("embedding", [])],
        )


@dataclass(slots=True)
class EmbeddingClient:
    """Lightweight wrapper around OpenAI's Embeddings endpoint."""

    model_name: str = "text-embedding-3-small"
    api_base_url: str = "https://api.openai.com/v1"
    timeout_seconds: int = 30
    _session: requests.Session = field(default_factory=requests.Session, init=False, repr=False)

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        """Return OpenAI embeddings for a batch of texts."""

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EmbeddingClientError(
                "Missing OPENAI_API_KEY environment variable. Please export your OpenAI API key "
                "before ingesting lecture documents."
            )

        endpoint = f"{self.api_base_url.rstrip('/')}/embeddings"
        payload = {"model": self.model_name, "input": list(texts)}
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = self._session.post(
                endpoint, json=payload, headers=headers, timeout=self.timeout_seconds
            )
            response.raise_for_status()
        except requests.exceptions.Timeout as exc:  # pragma: no cover - runtime scenario
            raise EmbeddingClientError(
                "Timed out while waiting for the OpenAI embeddings API. Please try again later."
            ) from exc
        except requests.exceptions.RequestException as exc:  # pragma: no cover - runtime scenario
            raise EmbeddingClientError(
                "An error occurred while communicating with the OpenAI embeddings API."
            ) from exc

        try:
            body = response.json()
        except json.JSONDecodeError as exc:  # pragma: no cover - runtime scenario
            raise EmbeddingClientError("Received an invalid JSON response from the OpenAI API.") from exc

        data = body.get("data")
        if not isinstance(data, list):
            raise EmbeddingClientError("The OpenAI API returned an unexpected response format.")

        embeddings: List[List[float]] = []
        for item in data:
            embedding = item.get("embedding") if isinstance(item, MutableMapping) else None
            if not isinstance(embedding, list):
                raise EmbeddingClientError(
                    "The OpenAI API returned an unexpected embedding payload."
                )
            embeddings.append([float(value) for value in embedding])

        return embeddings

    def close(self) -> None:
        """Close the underlying HTTP session."""

        self._session.close()

    def __enter__(self) -> "EmbeddingClient":  # pragma: no cover - convenience wrapper
        return self

    def __exit__(self, *_exc_info: Iterable[object]) -> None:  # pragma: no cover - convenience wrapper
        self.close()


@dataclass(slots=True)
class DocumentStore:
    """Persist embeddings for lecture documents and provide retrieval capabilities."""

    index_path: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "document_index.json"
    )
    _chunks: List[DocumentChunk] = field(default_factory=list, init=False, repr=False)
    _model_name: Optional[str] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        if self.index_path.is_file():
            self._load_index()

    # ------------------------------------------------------------------ Persistence
    def _load_index(self) -> None:
        try:
            payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DocumentStoreError(
                f"Failed to parse document index at {self.index_path}."
            ) from exc

        self._model_name = payload.get("model")
        chunks_payload = payload.get("chunks", [])
        if not isinstance(chunks_payload, list):
            raise DocumentStoreError("Document index is corrupted: expected a list of chunks.")

        self._chunks = [DocumentChunk.from_dict(item) for item in chunks_payload]

    def _save_index(self) -> None:
        payload = {
            "model": self._model_name,
            "chunks": [chunk.to_dict() for chunk in self._chunks],
        }
        self.index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # --------------------------------------------------------------------- Ingestion
    def ingest_pdf(
        self,
        pdf_path: Path,
        embedding_client: EmbeddingClient,
        *,
        title: str | None = None,
        chunk_size: int = 600,
        chunk_overlap: int = 120,
    ) -> DocumentMeta:
        """Extract text from a PDF, embed it, and persist the resulting chunks."""

        if not pdf_path.is_file():
            raise DocumentStoreError(f"Could not find PDF at {pdf_path}.")

        try:
            reader = PdfReader(str(pdf_path))
        except Exception as exc:  # pragma: no cover - runtime scenario
            raise DocumentStoreError(f"Failed to read PDF file: {pdf_path}.") from exc

        text_sections: List[str] = []
        for page in reader.pages:
            try:
                content = page.extract_text() or ""
            except Exception:  # pragma: no cover - runtime scenario
                content = ""
            cleaned = content.strip()
            if cleaned:
                text_sections.append(cleaned)

        document_text = "\n\n".join(text_sections)
        if not document_text.strip():
            raise DocumentStoreError("The supplied PDF does not contain any extractable text.")

        chunks = self._split_text(document_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not chunks:
            raise DocumentStoreError("Could not split the PDF into meaningful text chunks.")

        embeddings = embedding_client.embed(chunks)
        if len(embeddings) != len(chunks):
            raise DocumentStoreError("Embedding API returned an unexpected number of vectors.")

        document_id = str(uuid4())
        document_title = title or pdf_path.stem

        # Remove any previously stored chunks with the same title to avoid duplicates.
        self._chunks = [chunk for chunk in self._chunks if chunk.document_title != document_title]

        new_chunks: List[DocumentChunk] = []
        for index, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{document_id}:{index}"
            new_chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    document_title=document_title,
                    index=index,
                    text=chunk_text,
                    embedding=embedding,
                )
            )

        self._chunks.extend(new_chunks)
        self._model_name = embedding_client.model_name
        self._save_index()

        return DocumentMeta(
            document_id=document_id,
            title=document_title,
            source_path=str(pdf_path),
            chunk_count=len(new_chunks),
        )

    # --------------------------------------------------------------------- Retrieval
    def search(
        self, query: str, embedding_client: EmbeddingClient, *, top_k: int = 3
    ) -> List[Tuple[float, DocumentChunk]]:
        """Return the most relevant document chunks for the given query."""

        if not self._chunks:
            return []

        query_embedding = embedding_client.embed([query])[0]
        scored_chunks: List[Tuple[float, DocumentChunk]] = []
        for chunk in self._chunks:
            score = self._cosine_similarity(query_embedding, chunk.embedding)
            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda item: item[0], reverse=True)
        return scored_chunks[:top_k]

    def has_content(self) -> bool:
        """Return ``True`` when at least one document chunk is available."""

        return bool(self._chunks)

    @staticmethod
    def build_system_prompt(chunks: Sequence[DocumentChunk]) -> str:
        """Create a system prompt that injects lecture context into the chat."""

        intro = (
            "You are Neuro AI, a helpful study assistant for SLIIT students. Use the "
            "following lecture excerpts when formulating your answer. If the "
            "information is not present, acknowledge that you do not know."
        )
        sections: List[str] = [intro, "---"]
        for chunk in chunks:
            header = f"Source: {chunk.document_title} (section {chunk.index + 1})"
            sections.append(f"{header}\n{chunk.text}")
            sections.append("---")
        sections.append(
            "When answering, cite the relevant course material when possible and keep the "
            "focus on SLIIT curricula."
        )
        return "\n\n".join(sections)

    # ------------------------------------------------------------------ Text helpers
    @staticmethod
    def _split_text(text: str, *, chunk_size: int, chunk_overlap: int) -> List[str]:
        words = text.split()
        if not words:
            return []

        chunks: List[str] = []
        start = 0
        total_words = len(words)
        while start < total_words:
            end = min(start + chunk_size, total_words)
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words).strip()
            if chunk_text:
                chunks.append(chunk_text)
            if end == total_words:
                break
            start = max(0, end - chunk_overlap)
            if start >= total_words:
                break
        return chunks

    @staticmethod
    def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
        if not left or not right:
            return 0.0
        if len(left) != len(right):
            return 0.0

        dot = sum(a * b for a, b in zip(left, right))
        norm_left = math.sqrt(sum(value * value for value in left))
        norm_right = math.sqrt(sum(value * value for value in right))
        if norm_left == 0 or norm_right == 0:
            return 0.0
        return dot / (norm_left * norm_right)


__all__ = [
    "DocumentStore",
    "DocumentStoreError",
    "DocumentChunk",
    "DocumentMeta",
    "EmbeddingClient",
    "EmbeddingClientError",
]
