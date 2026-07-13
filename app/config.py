#variaveis de ambiente e configuração do app. Usado em app/main.py, app/routes/ask.py e app/routes/documents.py.

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=False)

BASE_DIR = Path(__file__).resolve().parent.parent

_TRUTHY = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    db_path: Path
    index_path: Path
    chunk_size: int
    chunk_overlap: int
    top_k: int
    relevance_threshold: float
    auto_seed: bool


def _build_settings() -> Settings:
    data_dir = Path(os.getenv("DOCUMIND_DATA_DIR", str(BASE_DIR / "data")))
    return Settings(
        data_dir=data_dir,
        db_path=Path(os.getenv("DOCUMIND_DB_PATH", str(data_dir / "documind.db"))),
        index_path=Path(os.getenv("DOCUMIND_INDEX_PATH", str(data_dir / "index.joblib"))),
        chunk_size=int(os.getenv("DOCUMIND_CHUNK_SIZE", "60")),
        chunk_overlap=int(os.getenv("DOCUMIND_CHUNK_OVERLAP", "15")),
        top_k=int(os.getenv("DOCUMIND_TOP_K", "3")),
        relevance_threshold=float(os.getenv("DOCUMIND_RELEVANCE_THRESHOLD", "0.1")),
        auto_seed=os.getenv("DOCUMIND_AUTO_SEED", "false").lower() in _TRUTHY,
    )


settings = _build_settings()