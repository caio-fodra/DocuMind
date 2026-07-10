#Rotas de cadastro e listagem de documentos
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from data.database import get_connection
from app.models import DocumentCreate, DocumentOut
from app.services.indexer import build_index, reindex_document

router = APIRouter(tags=["documents"])


def _get_document_out(doc_id: int) -> DocumentOut:
    # TODO: buscar em 'documents' a linha com id = doc_id (id, title, visibility,
    # created_at); se não existir, levantar HTTPException 404; caso contrário,
    # montar e retornar um DocumentOut a partir da linha.
    pass


@router.post("/documents", response_model=DocumentOut, status_code=201)
def create_document(payload: DocumentCreate) -> DocumentOut:
# TODO: inserir o documento (title, content, visibility) em 'documents' e obter
    # o doc_id gerado; chamar reindex_document(doc_id) para gerar os chunks e
    # build_index() para retreinar o TF-IDF; retornar _get_document_out(doc_id).
    pass


@router.get("/documents", response_model=list[DocumentOut])
def list_documents() -> list[DocumentOut]:
    # TODO: buscar em 'documents' todas as linhas (id, title, visibility,
    # created_at) ordenadas por id e retornar a lista de DocumentOut correspondente.
    pass