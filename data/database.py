#montar base de dados SQLite e tabelas, se não existirem. Usado no startup do app (lifespan) e nos testes.

from __future__ import annotations

import sqlite3

from app.config import settings


def get_connection() -> sqlite3.Connection:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT NOT NULL,
                content    TEXT NOT NULL,
                visibility TEXT NOT NULL DEFAULT 'public',
                category   TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            -- trechos derivados dos documentos (dado de busca, reconstruível)
            CREATE TABLE IF NOT EXISTS chunks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content     TEXT NOT NULL,
                UNIQUE (document_id, chunk_index),
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
            """
        )
        conn.commit()
    finally:
        conn.close()
