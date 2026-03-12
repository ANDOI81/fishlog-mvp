from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # .env is optional; production should use real env vars.
    pass


@dataclass(frozen=True)
class Settings:
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "change-me-please")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()
    DB_PATH: str = os.getenv(
        "DB_PATH",
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "app.db"),
    )
    BASE_URL: str = os.getenv("BASE_URL", "").strip()
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "https://app.fishpang.kr").strip()
    PRIMARY_DOMAIN: str = os.getenv("PRIMARY_DOMAIN", "fishpang.kr").strip().lower()
    APP_DOMAIN: str = os.getenv("APP_DOMAIN", "app.fishpang.kr").strip().lower()
    APP_ENV: str = os.getenv("APP_ENV", "local").strip().lower()
    DYNO: str = os.getenv("DYNO", "").strip()

    @property
    def is_production_like(self) -> bool:
        return bool(self.DYNO) or self.APP_ENV in {"prod", "production", "staging"}


settings = Settings()
