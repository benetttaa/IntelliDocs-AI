# IntelliDocs AI

IntelliDocs AI is an intelligent enterprise knowledge assistant that ingests document collections, indexes them for semantic retrieval, routes queries by intent, and answers grounded questions with citations.

## Highlights

- FastAPI backend with document upload endpoints and a query API
- Semantic chunking and embedding pipeline using sentence-transformers
- FAISS-based retrieval with reranking and abstention logic
- Logistic Regression + TF-IDF intent classifier
- React + Vite + Tailwind frontend for document ingestion and Q&A
- automated pytest coverage for backend API behavior

## Project structure

- `backend/` — Python FastAPI app and evaluation tests
- `frontend/` — Vite React frontend
- `.env.example` — environment template

## Quick start

### 1. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Frontend setup

```bash
cd frontend
npm install
```

### 3. Run the application

Terminal 1:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2:

```bash
cd frontend
npm run dev -- --host
```

The frontend runs on http://localhost:5173 and proxies API calls to the backend on http://localhost:8000.

## Environment variables

Create a `.env` file in the `backend` directory to configure optional LLM access:

```env
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o-mini
```

If no API key is configured, the app gracefully falls back to a grounded mock response while still returning citations from the indexed documents.

## Testing

```bash
cd backend
source .venv/bin/activate
pytest
```

## Notes

This project is designed to demonstrate production-minded RAG system architecture, retrieval quality, and backend/frontend integration while remaining lightweight and local-first for portfolio use.
