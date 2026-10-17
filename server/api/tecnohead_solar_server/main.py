"""Authenticated, single-client API endpoint for durable App synchronization."""

from __future__ import annotations

import hmac
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from . import __version__
from .db import alerts, history, insert_batch, migrate, summary
from .settings import ServerSettings

LOGGER = logging.getLogger("tecnohead_solar_server")
settings = ServerSettings.load()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not settings.database_url:
        raise RuntimeError("SOLAR_DATABASE_URL não configurada")
    if not settings.api_token:
        raise RuntimeError("SOLAR_API_TOKEN não configurado")
    migrate(settings)
    LOGGER.info("TecnoHead Solar server %s ready on schema %s", __version__, settings.db_schema)
    yield


app = FastAPI(title="TecnoHead Solar API", version=__version__, lifespan=lifespan)


async def authenticated(authorization: str | None = Header(default=None)) -> None:
    expected = settings.api_token
    if not expected:
        raise HTTPException(status_code=503, detail="API token não configurado")
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Token inválido")


class BatchPayload(BaseModel):
    installation_id: str
    readings: list[dict[str, Any]] = Field(min_length=1, max_length=1000)


@app.get("/api/v1/solar/health", dependencies=[Depends(authenticated)])
async def health() -> dict[str, Any]:
    summary_row = summary(settings)
    return {
        "ok": True,
        "service": "tecnohead_solar_server",
        "version": __version__,
        "schema": settings.db_schema,
        "readings": summary_row.get("readings", 0),
    }


@app.post("/api/v1/solar/readings/batch", dependencies=[Depends(authenticated)])
async def readings_batch(payload: BatchPayload) -> dict[str, Any]:
    try:
        acknowledged = insert_batch(settings, payload.installation_id, payload.readings)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True, "acknowledged_reading_ids": acknowledged, "count": len(acknowledged)}


@app.get("/api/v1/solar/history", dependencies=[Depends(authenticated)])
async def get_history(
    since_hours: int = Query(default=24, ge=1, le=24 * 31),
    limit: int = Query(default=500, ge=1, le=5000),
) -> dict[str, Any]:
    return {"source": "server_postgresql", "rows": history(settings, since_hours, limit)}


@app.get("/api/v1/solar/summary", dependencies=[Depends(authenticated)])
async def get_summary() -> dict[str, Any]:
    return summary(settings)


@app.get("/api/v1/solar/alerts", dependencies=[Depends(authenticated)])
async def get_alerts() -> dict[str, Any]:
    return {"source": "server_postgresql", "rows": alerts(settings)}

