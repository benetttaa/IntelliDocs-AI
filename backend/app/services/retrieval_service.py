from __future__ import annotations

from typing import Any

from app.services.embedding_service import EmbeddingService
from app.services.reranking_service import RerankingService
from app.services.vector_store import VectorStore


class RetrievalService:
    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStore, reranking_service: RerankingService):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.reranking_service = reranking_service

    def retrieve(self, question: str, top_k: int = 5) -> list[dict[str, Any]]:
        query_vector = self.embedding_service.embed_query(question)
        initial_hits = self.vector_store.search(query_vector, top_k=top_k)
        if not initial_hits:
            return []
        return self.reranking_service.rerank(question, initial_hits)
