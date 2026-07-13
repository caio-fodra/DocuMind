# CLI de reindexação: reprocessa todos os documentos e reconstrói o índice TF-IDF.
# Uso: python -m app.indexer
# A lógica de indexação vive em app/services/indexer.py; aqui é só o ponto de entrada.

from __future__ import annotations

from app.services.indexer import reindex_all


def main() -> None:
    docs, chunks = reindex_all()
    print(f"Indexação concluída: {docs} documento(s), {chunks} trecho(s) indexado(s).")


if __name__ == "__main__":
    main()
