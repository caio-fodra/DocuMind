from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from data.database import get_connection, init_db
from app.routes import ask, documents, health

logger = logging.getLogger("documind")
logging.basicConfig(level=logging.INFO)


def _auto_seed_if_empty() -> None:
    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) AS c FROM documents").fetchone()["c"]
    finally:
        conn.close()

    if count:
        return

    # Import tardio: evita puxar seed/indexer no caminho normal de startup.
    from data.seed import seed
    from app.services.indexer import reindex_all

    seed()
    docs, chunks = reindex_all()
    logger.info("Auto-seed: %d documento(s) e %d trecho(s) indexado(s).", docs, chunks)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.auto_seed:
        _auto_seed_if_empty()
    yield


app = FastAPI(
    title="DocuMind",
    version="0.1.0",
    description="Assistente inteligente de documentos (RAG em miniatura).",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(ask.router)