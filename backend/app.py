"""
Flask entrypoint for the Precision RAG backend.
"""

from __future__ import annotations

import logging
import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from backend.config import settings
from backend.services.ingest import process_pdf
from backend.services.query import execute_query


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Suppress ChromaDB telemetry errors (harmless but noisy)
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__)
    CORS(app)
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    settings.pdf_data_path.mkdir(parents=True, exist_ok=True)

    if not settings.gemini_api_key:
        logger.warning(
            "GEMINI_API_KEY is not set. /query requests will fail until it is configured."
        )

    @app.get("/health")
    def health() -> tuple[dict, int]:
        return {"status": "ok"}, 200

    @app.post("/upload")
    def upload_pdf() -> tuple[dict, int]:
        file = request.files.get("file")
        if not file:
            return {"error": "No file provided."}, 400

        filename = secure_filename(file.filename)
        if not filename.lower().endswith(".pdf"):
            return {"error": "Only PDF files are supported."}, 400

        target_path = settings.pdf_data_path / filename
        file.save(target_path)
        stats = process_pdf(target_path)
        return {"message": "Ingestion complete.", "stats": stats}, 200

    @app.post("/query")
    def query_rag() -> tuple[dict, int]:
        payload = request.get_json(force=True, silent=True) or {}
        question = (payload.get("question") or "").strip()
        if not question:
            return {"error": "The 'question' field is required."}, 400

        try:
            answer, citations, _chunks = execute_query(question)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Query pipeline failed.")
            return {"error": str(exc)}, 500

        response = {
            "answer_text": answer,
            "citations": citations,
        }
        return jsonify(response), 200

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)

