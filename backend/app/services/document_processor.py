from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path
from typing import Any

import fitz
from docx import Document as DocxDocument


class DocumentProcessor:
    def __init__(self, chunk_size: int = 500, overlap: int = 80):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _safe_text(self, value: str | None) -> str:
        if not value:
            return ""
        cleaned = value.replace("\r", " ")
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def _extract_pdf(self, file_bytes: bytes) -> str:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages: list[str] = []
        for page_number in range(len(doc)):
            page = doc.load_page(page_number)
            text = page.get_text("text")
            pages.append(f"\n[Page {page_number + 1}]\n{text}")
        doc.close()
        return "\n".join(pages)

    def _extract_docx(self, file_bytes: bytes) -> str:
        document = DocxDocument(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)

    def _extract_txt(self, file_bytes: bytes) -> str:
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("utf-8", errors="replace")

    def extract_text(self, file_name: str, file_bytes: bytes) -> str:
        lower_name = file_name.lower()
        if lower_name.endswith(".pdf"):
            return self._safe_text(self._extract_pdf(file_bytes))
        if lower_name.endswith(".docx"):
            return self._safe_text(self._extract_docx(file_bytes))
        if lower_name.endswith(".txt"):
            return self._safe_text(self._extract_txt(file_bytes))
        raise ValueError(f"Unsupported file type for: {file_name}")

    def chunk_text(self, text: str, file_name: str) -> list[dict[str, Any]]:
        if not text.strip():
            return []

        normalized = re.sub(r"\s+", " ", text)
        words = normalized.split()
        chunks: list[dict[str, Any]] = []
        start = 0
        chunk_index = 0

        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk_text = " ".join(words[start:end])
            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "source_name": file_name,
                    "page_number": None,
                }
            )
            chunk_index += 1
            if end == len(words):
                break
            start = max(start + self.chunk_size - self.overlap, start + 1)

        return chunks

    def process_upload(self, file_name: str, file_bytes: bytes, collection_name: str = "general") -> dict[str, Any]:
        text = self.extract_text(file_name, file_bytes)
        chunks = self.chunk_text(text, file_name)
        document_id = hashlib.sha256(f"{file_name}:{len(file_bytes)}:{len(text)}".encode("utf-8")).hexdigest()[:16]

        prepared_chunks = []
        for idx, chunk in enumerate(chunks):
            prepared_chunks.append(
                {
                    "chunk_id": f"{document_id}-{idx}",
                    "document_id": document_id,
                    "file_name": file_name,
                    "mime_type": self._mime_type(file_name),
                    "collection_name": collection_name,
                    "text": chunk["text"],
                    "page_number": chunk.get("page_number"),
                    "chunk_index": idx,
                    "source_name": file_name,
                }
            )

        return {
            "document_id": document_id,
            "file_name": file_name,
            "mime_type": self._mime_type(file_name),
            "collection_name": collection_name,
            "text": text,
            "chunks": prepared_chunks,
        }

    def _mime_type(self, file_name: str) -> str:
        lower_name = file_name.lower()
        if lower_name.endswith(".pdf"):
            return "application/pdf"
        if lower_name.endswith(".docx"):
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if lower_name.endswith(".txt"):
            return "text/plain"
        return "application/octet-stream"
