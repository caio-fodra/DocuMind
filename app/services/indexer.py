#indexacao com tf idf, chunking, persistencia em disco, reindexacao idempotente

from __future__ import annotations

from typing import Any

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

from app.config import settings
from app.database import get_connection
from app.services.chunking import chunk_text

#Stopwords pra reduzir ruído
PORTUGUESE_STOP_WORDS = [
    "a", "ao", "aos", "aquela", "aquelas", "aquele", "aqueles", "aquilo", "as",
    "ate", "com", "como", "da", "das", "de", "dela", "delas", "dele", "deles",
    "depois", "do", "dos", "e", "ela", "elas", "ele", "eles", "em", "entre",
    "era", "eram", "essa", "essas", "esse", "esses", "esta", "estas", "este",
    "estes", "eu", "foi", "foram", "ha", "isso", "isto", "ja", "la", "lhe",
    "lhes", "mais", "mas", "me", "mesmo", "meu", "meus", "minha", "minhas",
    "muito", "na", "nao", "nas", "nem", "no", "nos", "nossa", "nossas", "nosso",
    "nossos", "num", "numa", "o", "os", "ou", "para", "pela", "pelas", "pelo",
    "pelos", "por", "qual", "quais", "quando", "que", "quem", "sao", "se",
    "sem", "sempre", "sendo", "ser", "seu", "seus", "so", "sob", "sobre", "sua",
    "suas", "tambem", "te", "tem", "tinha", "tu", "tua", "tuas", "um", "uma",
    "umas", "uns", "voce", "voces",
]


def reindex_document(document_id: int) -> int:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT content FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Documento {document_id} não encontrado")

        conn.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
        pieces = chunk_text(row["content"], settings.chunk_size, settings.chunk_overlap)
        conn.executemany(
            "INSERT INTO chunks (document_id, chunk_index, content) VALUES (?, ?, ?)",
            [(document_id, i, piece) for i, piece in enumerate(pieces)],
        )
        conn.commit()
        return len(pieces)
    finally:
        conn.close()


def build_index() -> int:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT c.id AS chunk_id, c.document_id, c.chunk_index, c.content,
                   d.title, d.visibility, d.category
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            ORDER BY c.document_id, c.chunk_index
            """
        ).fetchall()
    finally:
        conn.close()

    settings.index_path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        if settings.index_path.exists():
            settings.index_path.unlink()
        return 0

    corpus = [r["content"] for r in rows]
    vectorizer = TfidfVectorizer(
        strip_accents="unicode",
        stop_words=PORTUGUESE_STOP_WORDS,
    )
    matrix = vectorizer.fit_transform(corpus)

    metadata = [
        {
            "chunk_id": r["chunk_id"],
            "document_id": r["document_id"],
            "chunk_index": r["chunk_index"],
            "title": r["title"],
            "visibility": r["visibility"],
            "category": r["category"],
            "content": r["content"],
        }
        for r in rows
    ]

    joblib.dump(
        {"vectorizer": vectorizer, "matrix": matrix, "metadata": metadata},
        settings.index_path,
    )
    return len(rows)


def load_index() -> dict[str, Any] | None:
    if not settings.index_path.exists():
        return None
    return joblib.load(settings.index_path)


def reindex_all() -> tuple[int, int]:
    conn = get_connection()
    try:
        doc_ids = [r["id"] for r in conn.execute("SELECT id FROM documents ORDER BY id")]
    finally:
        conn.close()

    for doc_id in doc_ids:
        reindex_document(doc_id)
    indexed = build_index()
    return len(doc_ids), indexed
