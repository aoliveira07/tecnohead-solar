"""Solar-specific alert rules with conservative false-positive handling."""

from __future__ import annotations

import uuid
from typing import Any

from .db import Database


def evaluate_collector(db: Database, installation_id: str, collector_id: str, reading: dict[str, Any]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    for channel in reading.get("channels", []):
        if not channel.get("supported"):
            continue
        # A channel that is explicitly disabled is not an error and is never
        # evaluated. The worker passes only enabled channels to this function.
        power = channel.get("power_dc_w")
        voltage = channel.get("voltage_v")
        current = channel.get("current_a")
        if power is None or voltage is None or current is None:
            continue
        if voltage < 5 and current < 0.5:
            continue  # night/idle/unoccupied; no false alarm
        if power < 15:
            alerts.append(
                {
                    "id": str(uuid.uuid4()),
                    "installation_id": installation_id,
                    "collector_id": collector_id,
                    "pv_input_id": channel.get("pv_input_id"),
                    "code": "pv_low_output",
                    "severity": "warning",
                    "title": f"PV{channel['channel']} com baixa produção",
                    "detail": "A entrada respondeu, mas está abaixo do limiar configurado; valide horário, sombra e comparação com painéis equivalentes.",
                    "context": {"power_dc_w": power, "voltage_v": voltage, "current_a": current},
                }
            )
    return alerts


def upsert_active_alerts(db: Database, candidates: list[dict[str, Any]]) -> None:
    for candidate in candidates:
        db.execute(
            """
            INSERT INTO alerts(id,installation_id,collector_id,pv_input_id,code,severity,title,detail,context)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT(installation_id,collector_id,pv_input_id,code,status)
            DO UPDATE SET detail=EXCLUDED.detail,context=EXCLUDED.context
            """,
            (
                candidate["id"], candidate["installation_id"], candidate.get("collector_id"),
                candidate.get("pv_input_id"), candidate["code"], candidate["severity"],
                candidate["title"], candidate["detail"], candidate.get("context", {}),
            ),
        )
