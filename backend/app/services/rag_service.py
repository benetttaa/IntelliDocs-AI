from __future__ import annotations

import time
from typing import Any

from app.core.config import get_settings
from app.models.schemas import ChatResponse, Citation
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.services.intent_classifier import IntentClassifier
from app.services.llm_service import LLMService
from app.services.reranking_service import RerankingService
from app.services.retrieval_service import RetrievalService
from app.services.vector_store import VectorStore


class RagService:
    def __init__(self):
        self.settings = get_settings()
        self.document_processor = DocumentProcessor()
        self.intent_classifier = IntentClassifier()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore(
            index_path="data/faiss_index.index",
            db_path="data/intellidocs.db",
        )
        self.reranking_service = RerankingService()
        self.retrieval_service = RetrievalService(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
            reranking_service=self.reranking_service,
        )
        self.llm_service = LLMService(api_key=self.settings.OPENAI_API_KEY, model=self.settings.OPENAI_MODEL)

    def process_document_upload(self, file_name: str, file_bytes: bytes, collection_name: str = "general") -> dict[str, Any]:
        result = self.document_processor.process_upload(file_name, file_bytes, collection_name)
        chunks = result["chunks"]
        embeddings = self.embedding_service.embed_texts([chunk["text"] for chunk in chunks])
        self.vector_store.add_document(
            document_id=result["document_id"],
            file_name=result["file_name"],
            mime_type=result["mime_type"],
            collection_name=result["collection_name"],
            chunk_records=chunks,
            embeddings=embeddings,
        )
        return result

    def answer_query(self, question: str, top_k: int = 5) -> ChatResponse:
        started = time.perf_counter()
        intent = self.intent_classifier.predict(question)
        retrieval = self.retrieval_service.retrieve(question, top_k=top_k)

        if not retrieval:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return ChatResponse(
                answer="I could not find sufficient evidence in the uploaded documents to answer this question with confidence.",
                citations=[],
                intent=intent,
                abstained=True,
                evidence_count=0,
                latency_ms=latency_ms,
            )

        answer_text = self.llm_service.generate_answer(question, retrieval)
        citations = [
            Citation(
                document_id=item["doc_id"],
                document_name=item["file_name"],
                page=item.get("page_number"),
                snippet=(item["text"][:200] + "..." if len(item["text"]) > 200 else item["text"]),
                score=float(item.get("score", 0.0)),
            )
            for item in retrieval
        ]
        latency_ms = int((time.perf_counter() - started) * 1000)

        return ChatResponse(
            answer=answer_text,
            citations=citations,
            intent=intent,
            abstained=False,
            evidence_count=len(retrieval),
            latency_ms=latency_ms,
            debug={"retrieval_hits": len(retrieval), "intent_confidence": self.intent_classifier.predict_proba(question)},
        )

    def list_documents(self) -> list[dict[str, Any]]:
        return self.vector_store.get_document_metadata()
