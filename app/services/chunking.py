# Funções de chunking de texto, usadas pelo indexador. Não conversam com banco/rede.

from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 60, overlap: int = 15) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size deve ser maior que zero")

    words = (text or "").split()
    if not words:
        return []

    overlap = max(0, min(overlap, chunk_size - 1))
    step = chunk_size - overlap

    chunks: list[str] = []
    start = 0
    total = len(words)
    while start < total:
        window = words[start : start + chunk_size]
        chunks.append(" ".join(window))
        if start + chunk_size >= total:
            break
        start += step
    return chunks
