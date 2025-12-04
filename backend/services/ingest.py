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

# Import OCR functionality (may not be available if dependencies are missing)
try:
    from backend.services.ocr import (
        OCR_AVAILABLE,
        extract_text_with_ocr_from_pdfplumber_page,
    )
except ImportError:
    OCR_AVAILABLE = False
    extract_text_with_ocr_from_pdfplumber_page = None  # type: ignore


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
    stats = {
        "pages": 0,
        "chunks_added": 0,
        "chunks_skipped": 0,
        "empty_pages": 0,
        "ocr_pages": 0,
    }

    with pdfplumber.open(pdf_path) as pdf:
        ocr_warning_logged = False
        for page_index, page in enumerate(pdf.pages):
            stats["pages"] += 1
            # Try multiple extraction methods
            raw_text = page.extract_text() or ""
            
            # Debug: Log what we got from first page
            if page_index == 0:
                logger.debug(f"Page 1 text extraction (normal): {len(raw_text)} characters")
            
            # Fallback: try extracting with layout preservation if normal extraction fails
            if not raw_text.strip():
                try:
                    raw_text = page.extract_text(layout=True) or ""
                    if page_index == 0:
                        logger.debug(f"Page 1 text extraction (layout): {len(raw_text)} characters")
                except Exception as e:
                    if page_index == 0:
                        logger.debug(f"Page 1 layout extraction failed: {e}")
            
            # Fallback: try extracting tables as text if still empty
            if not raw_text.strip():
                try:
                    tables = page.find_tables()
                    if tables:
                        table_texts = []
                        for table in page.extract_tables():
                            for row in table:
                                if row:
                                    table_texts.append(" ".join(str(cell) if cell else "" for cell in row))
                        raw_text = "\n".join(table_texts)
                        if page_index == 0:
                            logger.debug(f"Page 1 text extraction (tables): {len(raw_text)} characters")
                except Exception as e:
                    if page_index == 0:
                        logger.debug(f"Page 1 table extraction failed: {e}")
            
            # Final fallback: Use OCR for scanned/image-based pages
            if not raw_text.strip():
                if not OCR_AVAILABLE or extract_text_with_ocr_from_pdfplumber_page is None:
                    if not ocr_warning_logged:
                        logger.error(
                            "\n" + "=" * 70 + "\n"
                            "OCR DEPENDENCIES NOT AVAILABLE!\n"
                            "This PDF appears to be scanned (image-based).\n"
                            "To extract text from scanned PDFs, you MUST install:\n"
                            "\n"
                            "1. Python packages:\n"
                            "   pip install -r backend/requirements.txt\n"
                            "\n"
                            "2. Tesseract OCR (system binary):\n"
                            "   - Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
                            "   - macOS: brew install tesseract\n"
                            "   - Linux: sudo apt-get install tesseract-ocr\n"
                            "\n"
                            "3. Poppler (for PDF to image conversion):\n"
                            "   - Windows: https://github.com/oschwartz10612/poppler-windows/releases/\n"
                            "   - macOS: brew install poppler\n"
                            "   - Linux: sudo apt-get install poppler-utils\n"
                            "\n"
                            "Run 'python backend/check_ocr.py' to verify your setup.\n"
                            "See OCR_SETUP.md for detailed instructions.\n"
                            "=" * 70
                        )
                        ocr_warning_logged = True
                else:
                    try:
                        logger.info(f"Attempting OCR for page {page_index + 1} (scanned/image-based)")
                        ocr_text = extract_text_with_ocr_from_pdfplumber_page(pdf, page, page_index)
                        if ocr_text.strip():
                            raw_text = ocr_text
                            stats["ocr_pages"] += 1
                            logger.info(f"OCR successfully extracted {len(ocr_text)} characters from page {page_index + 1}")
                        else:
                            logger.warning(f"OCR returned no text for page {page_index + 1}")
                    except Exception as e:
                        logger.error(f"OCR failed for page {page_index + 1}: {e}", exc_info=True)
            
            normalized_text = _normalize_text(raw_text)
            if not normalized_text:
                stats["empty_pages"] += 1
                if page_index < 3:  # Log first few empty pages for debugging
                    logger.warning(
                        f"Page {page_index + 1} is empty (no extractable text even with OCR). "
                        "PDF may have quality issues or be unreadable."
                    )
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
        "Ingested %s: pages=%d added=%d skipped=%d empty=%d ocr=%d",
        pdf_path.name,
        stats["pages"],
        stats["chunks_added"],
        stats["chunks_skipped"],
        stats["empty_pages"],
        stats["ocr_pages"],
    )
    
    # Warn if all pages were empty
    if stats["empty_pages"] == stats["pages"] and stats["pages"] > 0:
        logger.warning(
            f"WARNING: All {stats['pages']} pages in {pdf_path.name} were empty. "
            "OCR was attempted but failed to extract text. "
            "The PDF may have quality issues or be unreadable."
        )
    elif stats["ocr_pages"] > 0:
        logger.info(
            f"OCR was used to extract text from {stats['ocr_pages']} scanned pages."
        )
    
    return stats


