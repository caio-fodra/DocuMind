# Rotas de cadastro e listagem de documentos.
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from data.database import get_connection
from app.models import DocumentCreate, DocumentOut
from app.services.indexer import build_index, reindex_document

router = APIRouter(tags=["documents"])

# Colunas expostas pela API (o 'content' completo fica fora da listagem, por ser pesado).
_SELECT_COLUMNS = "id, title, visibility, category, created_at"


def _get_document_out(doc_id: int) -> DocumentOut:
    conn = get_connection()
    try:
        row = conn.execute(
            f"SELECT {_SELECT_COLUMNS} FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    return DocumentOut(**dict(row))


@router.post("/documents", response_model=DocumentOut, status_code=201)
def create_document(payload: DocumentCreate) -> DocumentOut:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO documents (title, content, visibility, category) "
            "VALUES (?, ?, ?, ?)",
            (payload.title, payload.content, payload.visibility.value, payload.category),
        )
        conn.commit()
        doc_id = cursor.lastrowid
    finally:
        conn.close()

    # Indexação: gera os chunks do novo documento e retreina o TF-IDF sobre todo o
    # corpus. Ambos são idempotentes, então cadastrar é repetível sem duplicar dados.
    reindex_document(doc_id)
    build_index()

    return _get_document_out(doc_id)


@router.get("/documents", response_model=list[DocumentOut])
def list_documents() -> list[DocumentOut]:
    conn = get_connection()
    try:
        rows = conn.execute(
            f"SELECT {_SELECT_COLUMNS} FROM documents ORDER BY id"
        ).fetchall()
    finally:
        conn.close()

    return [DocumentOut(**dict(row)) for row in rows]