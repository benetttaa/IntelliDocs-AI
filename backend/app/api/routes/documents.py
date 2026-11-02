from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import UploadResponse
from app.services.rag_service import RagService

router = APIRouter(prefix="/documents", tags=["documents"])
rag_service = RagService()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required.")

    document_ids: list[str] = []
    chunk_count = 0

    for file in files:
        file_bytes = await file.read()
        processed = rag_service.process_document_upload(file.filename or "uploaded-document", file_bytes, collection_name="general")
        document_ids.append(processed["document_id"])
        chunk_count += len(processed["chunks"])

    return UploadResponse(
        message=f"Uploaded {len(files)} document(s) successfully.",
        document_ids=document_ids,
        chunk_count=chunk_count,
    )


@router.get("")
async def list_documents():
    return {"documents": rag_service.list_documents()}
