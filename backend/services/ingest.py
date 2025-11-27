"""
PDF ingestion utilities for Precision RAG.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import settings
from backend.vector_store.client import get_collection


logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    """Normalize whitespace in extracted PDF text."""
    return " ".join(text.split())


def _chunk_page_text(text: str) -> List[str]:
    """Chunk text for a single page using RecursiveCharacterTextSplitter."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.split_text(text)


def _find_chunk_bounds(
    page_text: str,
    chunk_text: str,
    search_start: int,
) -> Tuple[int, int, int]:
    """
    Locate character offsets for chunk_text within page_text.

    Returns (start, end, new_search_start).
    """
    idx = page_text.find(chunk_text, search_start)
    if idx == -1:
        idx = page_text.find(chunk_text)
    if idx == -1:
        # Fallback: treat as sequential chunk.
        idx = len(page_text)
    end_idx = idx + len(chunk_text)
    next_search = max(0, end_idx - settings.chunk_overlap)
    return idx, end_idx, next_search


def _chunk_sha(text: str) -> str:
    """Return SHA256 hash for deduplication."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def process_pdf(file_path: str | Path) -> Dict[str, int]:
    """
    Parse a PDF, chunk each page independently, and upsert into ChromaDB.
    """
    pdf_path = Path(file_path).resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    collection = get_collection()
    file_tag = hashlib.sha256(str(pdf_path).encode("utf-8")).hexdigest()[:12]
    stats = {"pages": 0, "chunks_added": 0, "chunks_skipped": 0, "empty_pages": 0}

    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            stats["pages"] += 1
            raw_text = page.extract_text() or ""
            normalized_text = _normalize_text(raw_text)
            if not normalized_text:
                stats["empty_pages"] += 1
                continue

            chunks = _chunk_page_text(normalized_text)
            search_start = 0
            payload: List[Dict[str, object]] = []
            ids: List[str] = []

            for chunk_idx, chunk_text in enumerate(chunks):
                char_start, char_end, search_start = _find_chunk_bounds(
                    normalized_text, chunk_text, search_start
                )
                chunk_id = (
                    f"{file_tag}_page_{page_index + 1}_chunk_{chunk_idx}_{char_start}"
                )
                payload.append(
                    {
                        "id": chunk_id,
                        "document": chunk_text,
                        "metadata": {
                            "source_file": pdf_path.name,
                            "page_number": page_index + 1,
                            "chunk_id": chunk_id,
                            "char_start": char_start,
                            "char_end": char_end,
                            "chunk_sha": _chunk_sha(chunk_text),
                        },
                    }
                )
                ids.append(chunk_id)

            existing = set()
            if ids:
                existing_response = collection.get(ids=ids)
                existing = set(existing_response.get("ids", []))

            to_add = [item for item in payload if item["id"] not in existing]
            if to_add:
                collection.add(
                    ids=[item["id"] for item in to_add],
                    documents=[str(item["document"]) for item in to_add],
                    metadatas=[item["metadata"] for item in to_add],
                )
                stats["chunks_added"] += len(to_add)
            stats["chunks_skipped"] += len(payload) - len(to_add)

    logger.info(
        "Ingested %s: pages=%d added=%d skipped=%d empty=%d",
        pdf_path.name,
        stats["pages"],
        stats["chunks_added"],
        stats["chunks_skipped"],
        stats["empty_pages"],
    )
    return stats


