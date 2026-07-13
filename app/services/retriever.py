#filtro de chunks de documentos baseado na similaridade com a pergunta do usuário. Usado em app/routes/ask.py.
from __future__ import annotations

from dataclasses import dataclass

from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings
from app.models import Visibility
from app.services.indexer import load_index


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: int
    title: str
    chunk_index: int
    content: str
    score: float


def _allowed_visibilities(profile: Visibility) -> set[str]:
    if profile == Visibility.internal:
        return {Visibility.public.value, Visibility.internal.value}
    return {Visibility.public.value}


def retrieve(
    question: str,
    profile: Visibility,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    index = load_index()
    if index is None:
        return []

    limit = settings.top_k if top_k is None else top_k
    allowed = _allowed_visibilities(profile)

    question_vector = index["vectorizer"].transform([question])
    scores = cosine_similarity(question_vector, index["matrix"])[0]

    candidates = [
        RetrievedChunk(
            document_id=meta["document_id"],
            title=meta["title"],
            chunk_index=meta["chunk_index"],
            content=meta["content"],
            score=float(score),
        )
        for meta, score in zip(index["metadata"], scores)
        if meta["visibility"] in allowed and score >= settings.relevance_threshold
    ]

    candidates.sort(key=lambda chunk: chunk.score, reverse=True)
    return candidates[:limit]