from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from data.database import init_db
from app.routes import ask, documents, health

logger = logging.getLogger("documind")
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
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