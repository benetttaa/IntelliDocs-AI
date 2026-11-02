from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import faiss
import numpy as np


class VectorStore:
    def __init__(self, index_path: str = "data/faiss_index.index", db_path: str = "data/intellidocs.db"):
        self.index_path = Path(index_path)
        self.db_path = Path(db_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._initialize_db()

        self.dimension = 384
        self.index = faiss.IndexFlatIP(self.dimension)
        self._items: list[dict[str, Any]] = []
        self._load_existing_index()

    def _initialize_db(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                mime_type TEXT,
                collection_name TEXT,
                uploaded_at TEXT,
                metadata TEXT
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT,
                file_name TEXT,
                collection_name TEXT,
                page_number INTEGER,
                chunk_index INTEGER,
                text TEXT,
                metadata TEXT,
                created_at TEXT
            )
            """
        )
        self.db.commit()

    def _load_existing_index(self) -> None:
        if self.index_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
            except Exception:
                self.index = faiss.IndexFlatIP(self.dimension)

        self._items = []
        rows = self.db.execute("SELECT chunk_id, doc_id, file_name, collection_name, page_number, chunk_index, text, metadata FROM chunks").fetchall()
        for row in rows:
            self._items.append(
                {
                    "chunk_id": row["chunk_id"],
                    "doc_id": row["doc_id"],
                    "file_name": row["file_name"],
                    "collection_name": row["collection_name"],
                    "page_number": row["page_number"],
                    "chunk_index": row["chunk_index"],
                    "text": row["text"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                }
            )

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        if embeddings.size == 0:
            return embeddings
        normalized = embeddings.astype("float32")
        faiss.normalize_L2(normalized)
        return normalized

    def add_document(self, document_id: str, file_name: str, mime_type: str, collection_name: str, chunk_records: list[dict[str, Any]], embeddings: np.ndarray):
        if not chunk_records:
            return
        if len(chunk_records) != len(embeddings):
            raise ValueError("Chunk count and embedding count differ.")

        self.db.execute(
            "INSERT OR REPLACE INTO documents (doc_id, file_name, mime_type, collection_name, uploaded_at, metadata) VALUES (?, ?, ?, ?, datetime('now'), ?)",
            (document_id, file_name, mime_type, collection_name, json.dumps({"chunks": len(chunk_records)})),
        )

        normalized = self._normalize(embeddings)
        self.index.add(normalized)

        for record in chunk_records:
            chunk_id = record["chunk_id"]
            self.db.execute(
                "INSERT OR REPLACE INTO chunks (chunk_id, doc_id, file_name, collection_name, page_number, chunk_index, text, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                (
                    chunk_id,
                    record["document_id"],
                    record["file_name"],
                    record["collection_name"],
                    record.get("page_number"),
                    record["chunk_index"],
                    record["text"],
                    json.dumps({"source_name": record.get("source_name", file_name), "metadata": record.get("metadata", {})}),
                ),
            )
            self._items.append(
                {
                    "chunk_id": chunk_id,
                    "doc_id": record["document_id"],
                    "file_name": file_name,
                    "collection_name": collection_name,
                    "page_number": record.get("page_number"),
                    "chunk_index": record["chunk_index"],
                    "text": record["text"],
                    "metadata": {"source_name": record.get("source_name", file_name)},
                }
            )

        self.db.commit()
        self._persist_index()

    def _persist_index(self) -> None:
        faiss.write_index(self.index, str(self.index_path))

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> list[dict[str, Any]]:
        if self.index.ntotal == 0:
            return []

        normalized_query = self._normalize(np.asarray([query_vector], dtype="float32"))
        distances, indices = self.index.search(normalized_query, min(top_k, self.index.ntotal))
        results: list[dict[str, Any]] = []

        for idx, score in zip(indices[0], distances[0]):
            if idx < 0:
                continue
            payload = self._items[int(idx)]
            results.append({
                "chunk_id": payload["chunk_id"],
                "doc_id": payload["doc_id"],
                "file_name": payload["file_name"],
                "collection_name": payload["collection_name"],
                "page_number": payload["page_number"],
                "chunk_index": payload["chunk_index"],
                "text": payload["text"],
                "score": float(score),
                "metadata": payload.get("metadata", {}),
            })

        return results

    def get_document_metadata(self) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT doc_id, file_name, mime_type, collection_name, uploaded_at, metadata FROM documents ORDER BY uploaded_at DESC").fetchall()
        documents = []
        for row in rows:
            documents.append({
                "doc_id": row["doc_id"],
                "file_name": row["file_name"],
                "mime_type": row["mime_type"],
                "collection_name": row["collection_name"],
                "uploaded_at": row["uploaded_at"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            })
        return documents
