"""Optional authenticated API synchronization with durable ACK handling."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .db import Database
from .store import mark_batch_ack, mark_batch_attempt, pending_batch

LOGGER = logging.getLogger("tecnohead_solar.sync")


def _safe_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


async def health_check(base_url: str, token: str) -> dict[str, Any]:
    if not base_url or not token:
        return {"state": "disabled", "detail": "API externa não configurada"}
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=False) as client:
            response = await client.get(
                _safe_url(base_url, "/api/v1/solar/health"),
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.is_success:
            return {"state": "online", "detail": "API respondeu"}
        return {"state": "offline", "detail": f"HTTP {response.status_code}"}
    except (httpx.HTTPError, OSError) as exc:
        return {"state": "offline", "detail": type(exc).__name__}


async def remote_history(base_url: str, token: str, since_hours: int, limit: int) -> list[dict[str, Any]]:
    if not base_url or not token:
        return []
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=False) as client:
            response = await client.get(
                _safe_url(base_url, "/api/v1/solar/history"),
                params={"since_hours": since_hours, "limit": limit},
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.is_success:
            body = response.json()
            return body.get("rows", []) if isinstance(body, dict) else []
    except (httpx.HTTPError, OSError, ValueError):
        LOGGER.debug("Remote Solar history unavailable", exc_info=True)
    return []


async def sync_once(db: Database, base_url: str, token: str, installation_id: str) -> dict[str, Any]:
    batch = pending_batch(db, 200)
    if not base_url or not token:
        return {"state": "disabled", "sent": 0, "pending": len(batch)}
    if not batch:
        return {"state": "online", "sent": 0, "pending": 0}
    reading_ids = [str(row["reading_id"]) for row in batch]
    payload = {"installation_id": installation_id, "readings": batch}
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            response = await client.post(
                _safe_url(base_url, "/api/v1/solar/readings/batch"),
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
            )
        if response.is_success:
            body = response.json()
            acknowledged = [str(value) for value in body.get("acknowledged_reading_ids", reading_ids)]
            mark_batch_ack(db, acknowledged)
            mark_batch_attempt(db, [value for value in reading_ids if value not in acknowledged])
            return {"state": "online", "sent": len(acknowledged), "pending": len(batch) - len(acknowledged)}
        mark_batch_attempt(db, reading_ids, f"HTTP {response.status_code}")
        return {"state": "offline", "sent": 0, "pending": len(batch)}
    except (httpx.HTTPError, OSError, ValueError) as exc:
        mark_batch_attempt(db, reading_ids, type(exc).__name__)
        LOGGER.warning("Solar API sync failed: %s", type(exc).__name__)
        return {"state": "offline", "sent": 0, "pending": len(batch)}
