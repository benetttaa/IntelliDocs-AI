from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import ChatResponse, QueryRequest
from app.services.rag_service import RagService

router = APIRouter(prefix="/chat", tags=["chat"])
rag_service = RagService()


@router.post("", response_model=ChatResponse)
async def ask_question(payload: QueryRequest):
    return rag_service.answer_query(payload.question, top_k=payload.top_k)
