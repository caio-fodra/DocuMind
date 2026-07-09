#rota de pergunta e resposta
from __future__ import annotations

from fastapi import APIRouter

from app.models import AskRequest, AskResponse, Source
from app.services.llm import generate_answer
from app.services.retriever import retrieve

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    #TODO: recuperar os chunks relevantes via retrieve(payload.question, payload.top_k); 
    # gerar a resposta via generate_answer(payload.question, chunks); montar e retornar 
    # o AskResponse.
    pass