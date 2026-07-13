from __future__ import annotations

import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models import Confidence
from app.services.indexer import PORTUGUESE_STOP_WORDS
from app.services.prompt_guard import redact, sanitize_sentences
from app.services.retriever import RetrievedChunk

NAO_SEI = "Não sei responder com base nos documentos disponíveis."
HIGH_CONFIDENCE_SCORE = 0.30
MAX_SENTENCES = 2
MAX_SOURCE_CHUNKS = 2
MIN_SENTENCE_CHARS = 15
SECONDARY_SENTENCE_RATIO = 0.5

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def generate_answer(
    question: str, chunks: list[RetrievedChunk]
) -> tuple[str, Confidence]:
    if not chunks:
        return NAO_SEI, Confidence.none

    top_doc = chunks[0].document_id
    source_chunks = [
        c for c in chunks[:MAX_SOURCE_CHUNKS] if c.document_id == top_doc
    ]

    answer = redact(_extract_answer(question, source_chunks))
    if not answer.strip():
        return NAO_SEI, Confidence.none

    confidence = (
        Confidence.high
        if chunks[0].score >= HIGH_CONFIDENCE_SCORE
        else Confidence.low
    )

    return answer, confidence


def _split_sentences(text: str) -> list[str]:
    sentences = _SENTENCE_BOUNDARY.split(text.strip())
    return [s.strip() for s in sentences if len(s.strip()) >= MIN_SENTENCE_CHARS]


def _extract_answer(question: str, chunks: list[RetrievedChunk]) -> str:
    sentences: list[str] = []
    for chunk in chunks:
        sentences.extend(_split_sentences(chunk.content))

    sentences = sanitize_sentences(sentences)

    if not sentences:
        return ""

    try:
        vectorizer = TfidfVectorizer(
            strip_accents="unicode",
            stop_words=PORTUGUESE_STOP_WORDS,
        )
        matrix = vectorizer.fit_transform([question, *sentences])
    except ValueError:
        return ""

    scores = cosine_similarity(matrix[0], matrix[1:])[0]
    ranked = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)

    top_score = scores[ranked[0]]
    if top_score <= 0:
        return ""

    selected: list[str] = []
    for i in ranked:
        if scores[i] <= 0:
            break
        if selected and scores[i] < SECONDARY_SENTENCE_RATIO * top_score:
            break
        sentence = sentences[i]
        if sentence not in selected:
            selected.append(sentence)
        if len(selected) >= MAX_SENTENCES:
            break

    return " ".join(selected)