#indexacao com tf idf, chunking, persistencia em disco, reindexacao idempotente

from __future__ import annotations

from app.services.indexer import reindex_all


def main() -> None:
    docs, chunks = reindex_all()
    print(f"Indexação concluída: {docs} documento(s), {chunks} trecho(s) indexado(s).")


if __name__ == "__main__":
    main()
