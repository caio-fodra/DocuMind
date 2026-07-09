#variaveis de ambiente e configuração do app. Usado em app/main.py, app/services/ask.py e app/services/documents.py.

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    db_path: Path


def _build_settings() -> Settings:
    data_dir = Path(os.getenv("DOCUMIND_DATA_DIR", str(BASE_DIR / "data")))
    return Settings(
        data_dir=data_dir,
        db_path=Path(os.getenv("DOCUMIND_DB_PATH", str(data_dir / "documind.db"))),
    )


settings = _build_settings()
