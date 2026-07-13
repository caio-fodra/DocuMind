from __future__ import annotations

from data.database import get_connection
from app.services.indexer import reindex_all


def _count_chunks() -> int:
    conn = get_connection()
    try:
        return conn.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()["n"]
    finally:
        conn.close()


def test_create_document_returns_metadata(client):
    payload = {
        "title": "Serviço Fictício Nova",
        "content": "Documento fictício de teste com conteúdo suficiente para indexar.",
        "visibility": "public",
        "category": "manual",
    }
    resp = client.post("/documents", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert isinstance(body["id"], int)
    assert body["title"] == payload["title"]
    assert body["visibility"] == "public"
    assert body["category"] == "manual"
    assert body["created_at"]


def test_create_document_validation_errors(client):
    resp = client.post("/documents", json={"title": "", "content": "x"})
    assert resp.status_code == 422
    assert "Traceback" not in resp.text
    assert "detail" in resp.json()


def test_list_documents(client):
    resp = client.get("/documents")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    titles = {d["title"] for d in body}
    assert {"Serviço Vega", "Portal Atlas"} <= titles


def test_reindex_is_idempotent(client):
    docs_before, chunks_before = reindex_all()
    docs_after, chunks_after = reindex_all()
    assert docs_before == docs_after
    assert chunks_before == chunks_after
    assert _count_chunks() == chunks_after