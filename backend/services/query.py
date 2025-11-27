"""
Query and response utilities for Precision RAG.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Tuple

import google.generativeai as genai

from backend.config import settings
from backend.vector_store.client import get_collection


logger = logging.getLogger(__name__)
CITATION_PATTERN = re.compile(r"\[Ref:\s*Page\s*(\d+)\]")


def _configure_gemini() -> genai.GenerativeModel:
    """Configure and cache the Gemini model."""
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config={
            "temperature": 0.0,
            "top_k": 1,
            "max_output_tokens": 1024,
        },
        safety_settings=[
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            }
        ],
    )


_gemini_model: genai.GenerativeModel | None = None


def _get_model() -> genai.GenerativeModel:
    global _gemini_model
    if _gemini_model is None:
        _gemini_model = _configure_gemini()
    return _gemini_model


def retrieve_chunks(query: str, limit: int = 15, max_chars: int = 12000) -> List[Dict]:
    """Fetch the most relevant chunks from Chroma."""
    collection = get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=limit,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]

    combined: List[Dict] = []
    for doc, metadata, chunk_id, distance in zip(
        documents, metadatas, ids, distances, strict=False
    ):
        combined.append(
            {
                "id": chunk_id,
                "document": doc,
                "metadata": metadata,
                "distance": distance,
            }
        )

    total_chars = 0
    filtered: List[Dict] = []
    for chunk in combined:
        doc_len = len(chunk["document"])
        if total_chars + doc_len > max_chars:
            break
        filtered.append(chunk)
        total_chars += doc_len

    return filtered


def build_context(chunks: List[Dict]) -> str:
    """Format retrieved chunks for the Gemini prompt."""
    formatted = []
    for chunk in chunks:
        metadata = chunk["metadata"]
        formatted.append(
            f"[Source: {metadata['source_file']}, Page: {metadata['page_number']}] "
            f"{chunk['document']}"
        )
    return "\n".join(formatted)


def build_prompt(user_query: str, context: str) -> str:
    """Construct the final prompt, embedding the system instructions."""
    system_prompt = (
        "You are a precision-focused technical auditor. Your goal is to answer "
        "questions based ONLY on the provided context snippets.\n\n"
        "INPUT CONTEXT FORMAT:\n"
        "[Source: {filename}, Page: {page_number}] {content}\n\n"
        "INSTRUCTIONS:\n"
        "1. Strict Grounding: Do not use outside knowledge. If the answer is "
        'not in the context, state "I cannot find this information in the provided documents."\n'
        "2. Citation Requirement: Every single claim or factual statement must "
        "be immediately followed by a citation reference in the format [Ref: Page X].\n"
        "3. Synthesis: If multiple pages contain the answer, combine them and cite both.\n"
        "4. Tone: Professional, objective, and concise.\n"
    )
    return (
        f"{system_prompt}\n"
        f"USER QUESTION: {user_query}\n\n"
        f"CONTEXT:\n{context}"
    )


def call_gemini(prompt: str) -> str:
    """Invoke Gemini 2.5 Flash with the constructed prompt."""
    model = _get_model()
    response = model.generate_content(prompt)
    if not response.text:
        raise RuntimeError("No text returned from Gemini.")
    return response.text.strip()


def build_citations(answer: str, chunks: List[Dict]) -> List[Dict]:
    """Map `[Ref: Page X]` markers to actual chunk metadata."""
    citations: List[Dict] = []
    page_to_chunk: Dict[int, Dict] = {}
    for chunk in chunks:
        page_to_chunk.setdefault(chunk["metadata"]["page_number"], chunk)

    for idx, match in enumerate(CITATION_PATTERN.finditer(answer), start=1):
        page_num = int(match.group(1))
        chunk = page_to_chunk.get(page_num)
        if not chunk:
            continue
        metadata = chunk["metadata"]
        snippet = chunk["document"][:250] + ("..." if len(chunk["document"]) > 250 else "")
        citations.append(
            {
                "id": idx,
                "source_file": metadata["source_file"],
                "page_number": metadata["page_number"],
                "snippet": snippet,
            }
        )

    if not citations and chunks:
        top = chunks[0]["metadata"]
        fallback_snippet = chunks[0]["document"][:250]
        citations.append(
            {
                "id": 1,
                "source_file": top["source_file"],
                "page_number": top["page_number"],
                "snippet": fallback_snippet,
            }
        )

    return citations


def execute_query(user_query: str) -> Tuple[str, List[Dict], List[Dict]]:
    """
    Full retrieval + generation pipeline.
    Returns answer text, citations, and raw chunks for debugging.
    """
    chunks = retrieve_chunks(user_query)
    if not chunks:
        return (
            "I cannot find this information in the provided documents.",
            [],
            [],
        )

    context = build_context(chunks)
    prompt = build_prompt(user_query, context)
    answer = call_gemini(prompt)
    citations = build_citations(answer, chunks)
    return answer, citations, chunks

