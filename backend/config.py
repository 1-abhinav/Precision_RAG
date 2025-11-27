"""
Configuration module for the Precision RAG backend.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    """Centralized configuration object."""

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    chroma_path: Path = BASE_DIR / "vector_store"
    pdf_data_path: Path = (BASE_DIR / ".." / "data" / "pdfs").resolve()
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    collection_name: str = os.getenv("CHROMA_COLLECTION", "engineering_docs")

    def validate(self) -> None:
        if not self.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Please add it to your .env file."
            )

        self.chroma_path.mkdir(parents=True, exist_ok=True)
        Path(self.pdf_data_path).mkdir(parents=True, exist_ok=True)


settings = Settings()

