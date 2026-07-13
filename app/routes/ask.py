#rota de pergunta e resposta
from __future__ import annotations

from fastapi import APIRouter

from app.models import AskRequest, AskResponse, Source
from app.services.llm import generate_answer
from app.services.retriever import retrieve

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    chunks = retrieve(payload.question, payload.profile)
    answer, confidence = generate_answer(payload.question, chunks)
    sources = [
        Source(
            document_id=chunk.document_id,
            title=chunk.title,
            chunk_index=chunk.chunk_index,
            score=chunk.score,
        )
        for chunk in chunks
    ]
    return AskResponse(answer=answer, confidence=confidence, sources=sources)