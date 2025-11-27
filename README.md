# Precision RAG

Local citation-aware Retrieval Augmented Generation (RAG) stack for engineering PDFs.

## Project Structure

```
Precision_RAG/
├─ backend/               # Flask application
│  ├─ app.py
│  ├─ config.py
│  └─ services/
├─ frontend/              # React (Vite) client
├─ data/pdfs/             # Ingested PDFs live here
└─ vector_store/          # ChromaDB persistence
```

## Backend Setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy ..\env.sample .env  # set GEMINI_API_KEY
flask --app app run --debug
```

### Ingestion

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5000/upload -Method Post `
  -InFile ".\data\pdfs\Structural_Specs.pdf" `
  -ContentType "multipart/form-data"
```

### Query

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5000/query -Method Post `
  -Body (@{ question = "What is the concrete grade?" } | ConvertTo-Json) `
  -ContentType "application/json"
```

## Frontend Setup

```powershell
cd frontend
npm install
npm run dev -- --host
```

Set `VITE_API_BASE_URL=http://127.0.0.1:5000` in `frontend/.env` (or create from `.env.example`).

The frontend includes:
- **Chat Interface**: Interactive Q&A with your documents
- **Citation Renderer**: Displays source file and page numbers for each answer
- **PDF Upload**: Drag-and-drop or click to upload engineering PDFs
- **Modern UI**: Clean, professional design with dark mode support

## Testing

- `pytest` inside `backend/` for ingestion helpers (to be added).
- React Testing Library for `CitationRenderer` (to be added).

## Features

✅ **Complete Frontend UI**: React-based chat interface with citation rendering  
✅ **PDF Ingestion**: Upload and process engineering PDFs with page-level chunking  
✅ **Citation-Aware RAG**: Answers include source file and page number citations  
✅ **Vector Search**: Semantic search using ChromaDB with sentence transformers  
✅ **Modern UI**: Responsive design with dark mode support  

## Next Steps

- Add automated ingestion CLI + regression tests.
- Plan for docker/nginx once local workflow stabilizes.
- Optional: PDF viewer component for inline document viewing.

