# Definição de visibilidade e confiança.
# Modelos de entrada e saída para documentos e perguntas.

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Visibility(str, Enum):
    public = "public"
    internal = "internal"


class Confidence(str, Enum):
    high = "high"
    low = "low"
    none = "none"


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., min_length=1)
    visibility: Visibility = Visibility.public
    category: str | None = Field(default=None, max_length=100)


class DocumentOut(BaseModel):
    id: int
    title: str
    visibility: Visibility
    category: str | None = None
    created_at: str


class Source(BaseModel):
    document_id: int
    title: str
    chunk_index: int
    score: float


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    profile: Visibility = Field(
        default=Visibility.public,
        description="Perfil de acesso: 'public' vê só públicos; 'internal' vê públicos + internos.",
    )


class AskResponse(BaseModel):
    answer: str
    confidence: Confidence
    sources: list[Source]
