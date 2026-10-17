"""Environment-only settings for the optional per-client server module."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


def safe_identifier(value: str, default: str = "solar") -> str:
    candidate = (value or default).strip().lower()
    if not IDENTIFIER.fullmatch(candidate):
        raise ValueError("SOLAR_DB_SCHEMA must contain only lowercase letters, digits and underscores")
    return candidate


@dataclass(frozen=True, slots=True)
class ServerSettings:
    database_url: str
    api_token: str
    db_schema: str = "solar"
    retention_days: int = 7
    bind_host: str = "127.0.0.1"
    bind_port: int = 18081

    @classmethod
    def load(cls) -> ServerSettings:
        return cls(
            database_url=os.getenv("SOLAR_DATABASE_URL", "").strip(),
            api_token=os.getenv("SOLAR_API_TOKEN", ""),
            db_schema=safe_identifier(os.getenv("SOLAR_DB_SCHEMA", "solar")),
            retention_days=max(1, min(3650, int(os.getenv("SOLAR_RETENTION_DAYS", "7")))),
            bind_host=os.getenv("SOLAR_BIND_HOST", "127.0.0.1"),
            bind_port=max(1, min(65535, int(os.getenv("SOLAR_PORT", "18081")))),
        )

