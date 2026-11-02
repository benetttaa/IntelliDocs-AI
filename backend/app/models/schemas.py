from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChunkRecord(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    page_number: int | None = None
    chunk_index: int = 0
    source_name: str
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    document_id: str
    document_name: str
    page: int | None = None
    snippet: str
    score: float = 0.0


class UploadRequest(BaseModel):
    collection: str = "general"


class UploadResponse(BaseModel):
    message: str
    document_ids: list[str]
    chunk_count: int


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = 5


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    intent: str
    abstained: bool = False
    evidence_count: int = 0
    latency_ms: int = 0
    debug: dict[str, Any] | None = None


class EvaluationSummary(BaseModel):
    total_queries: int
    average_recall: float
    average_latency_ms: float
    top_intent: str
    dataset_name: str


class HealthStatus(BaseModel):
    status: Literal["ok"]
    app: str
    version: str
