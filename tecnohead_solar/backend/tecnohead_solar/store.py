"""Application data access helpers shared by the web app and worker."""

from __future__ import annotations

import csv
import io
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from .db import Database


def now_utc() -> datetime:
    return datetime.now(UTC)


def as_iso(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, dict):
        return {key: as_iso(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_iso(item) for item in value]
    return value


def serialize(row: dict[str, Any]) -> dict[str, Any]:
    return {key: as_iso(value) for key, value in row.items()}


def installation(db: Database) -> dict[str, Any] | None:
    row = db.fetch_one("SELECT * FROM installations ORDER BY created_at LIMIT 1")
    return serialize(row) if row else None


def collectors(db: Database) -> list[dict[str, Any]]:
    rows = db.fetch_all(
        """
        SELECT c.*, count(p.id)::int AS pv_count,
               count(p.id) FILTER (WHERE p.enabled)::int AS enabled_pv_count
        FROM collectors c LEFT JOIN pv_inputs p ON p.collector_id = c.id
        GROUP BY c.id ORDER BY c.name, c.ip::text
        """
    )
    return [serialize(row) for row in rows]


def collector_detail(db: Database, collector_id: str) -> dict[str, Any] | None:
    collector = db.fetch_one("SELECT * FROM collectors WHERE id=%s", (collector_id,))
    if not collector:
        return None
    payload = serialize(collector)
    payload["pv_inputs"] = [
        serialize(row)
        for row in db.fetch_all(
            "SELECT * FROM pv_inputs WHERE collector_id=%s ORDER BY channel", (collector_id,)
        )
    ]
    payload["recent_readings"] = [
        serialize(row)
        for row in db.fetch_all(
            """
            SELECT r.*, p.channel, p.name AS pv_name
            FROM readings r LEFT JOIN pv_inputs p ON p.id=r.pv_input_id
            WHERE r.collector_id=%s ORDER BY r.captured_at DESC LIMIT 120
            """,
            (collector_id,),
        )
    ]
    return payload


def pv_inputs(db: Database) -> list[dict[str, Any]]:
    return [
        serialize(row)
        for row in db.fetch_all(
            """
            SELECT p.*, c.name AS collector_name, c.ip, c.logger_serial
            FROM pv_inputs p JOIN collectors c ON c.id=p.collector_id
            ORDER BY c.name, p.channel
            """
        )
    ]


def setup_installation(db: Database, payload: dict[str, Any]) -> dict[str, Any]:
    installation_id = uuid.UUID(str(payload.get("installation_id") or uuid.uuid4()))
    name = str(payload.get("name") or "Minha instalação solar").strip()[:120]
    timezone_name = str(payload.get("timezone") or "UTC").strip()[:80]
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    db.execute(
        """
        INSERT INTO installations(id,name,timezone,latitude,longitude)
        VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT(id) DO UPDATE SET name=EXCLUDED.name, timezone=EXCLUDED.timezone,
          latitude=EXCLUDED.latitude, longitude=EXCLUDED.longitude, updated_at=now()
        """,
        (installation_id, name, timezone_name, latitude, longitude),
    )

    for item in payload.get("collectors", []):
        requested_id = item.get("id")
        existing = None
        if requested_id:
            existing = db.fetch_one("SELECT id FROM collectors WHERE id=%s", (requested_id,))
        if not existing:
            existing = db.fetch_one(
                "SELECT id FROM collectors WHERE installation_id=%s AND logger_serial=%s",
                (installation_id, int(item["logger_serial"])),
            )
        collector_id = uuid.UUID(str(existing["id"] if existing else requested_id or uuid.uuid4()))
        logger_serial = int(item["logger_serial"])
        db.execute(
            """
            INSERT INTO collectors(id,installation_id,name,ip,port,logger_serial,inverter_serial,profile,slave_id,enabled)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT(id) DO UPDATE SET name=EXCLUDED.name,ip=EXCLUDED.ip,port=EXCLUDED.port,
              logger_serial=EXCLUDED.logger_serial,inverter_serial=EXCLUDED.inverter_serial,
              profile=EXCLUDED.profile,slave_id=EXCLUDED.slave_id,enabled=EXCLUDED.enabled,updated_at=now()
            """,
            (
                collector_id,
                installation_id,
                str(item.get("name") or f"Microinversor {logger_serial}")[:120],
                str(item["ip"]),
                int(item.get("port") or 8899),
                logger_serial,
                str(item.get("inverter_serial") or "") or None,
                str(item.get("profile") or "deye_micro_v1"),
                int(item.get("slave_id") or 1),
                bool(item.get("enabled", True)),
            ),
        )
        for channel in range(1, 5):
            pv = next(
                (candidate for candidate in item.get("pv_inputs", []) if int(candidate.get("channel", 0)) == channel),
                {},
            )
            pv_id = uuid.UUID(str(pv.get("id") or uuid.uuid4()))
            db.execute(
                """
                INSERT INTO pv_inputs(id,collector_id,channel,name,enabled,physical_location,wp,azimuth,tilt,shade_factor,map_x,map_y)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(collector_id,channel) DO UPDATE SET name=EXCLUDED.name,enabled=EXCLUDED.enabled,
                  physical_location=EXCLUDED.physical_location,wp=EXCLUDED.wp,azimuth=EXCLUDED.azimuth,
                  tilt=EXCLUDED.tilt,shade_factor=EXCLUDED.shade_factor,map_x=EXCLUDED.map_x,map_y=EXCLUDED.map_y,
                  updated_at=now()
                """,
                (
                    pv_id,
                    collector_id,
                    channel,
                    str(pv.get("name") or f"PV{channel}")[:120],
                    bool(pv.get("enabled", True)),
                    str(pv.get("physical_location") or "")[:160] or None,
                    pv.get("wp"),
                    pv.get("azimuth"),
                    pv.get("tilt"),
                    pv.get("shade_factor", 1),
                    pv.get("map_x", channel * 20),
                    pv.get("map_y", 30),
                ),
            )
    return installation(db) or {}


def save_collector_probe(db: Database, collector_id: str, status: str, payload: dict[str, Any], error: str | None = None) -> None:
    db.execute(
        """
        UPDATE collectors SET last_seen_at=CASE WHEN %s='online' THEN now() ELSE last_seen_at END,
          last_status=%s,last_error=%s,last_payload=%s,updated_at=now() WHERE id=%s
        """,
        (status, status, error, payload, collector_id),
    )


def save_reading(
    db: Database,
    *,
    reading_id: uuid.UUID,
    installation_id: str,
    collector_id: str,
    pv_input_id: str | None,
    captured_at: datetime,
    metrics: dict[str, Any],
    raw_payload: dict[str, Any],
    sync_state: str,
) -> None:
    with db.connection() as connection, connection.transaction():
        connection.execute(
            """
                INSERT INTO readings(
                  reading_id,installation_id,collector_id,pv_input_id,captured_at,power_ac_w,
                  energy_today_kwh,energy_total_kwh,voltage_v,current_a,power_dc_w,frequency_hz,
                  temperature_c,status,quality,source,sync_state,raw_payload
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(reading_id) DO UPDATE SET received_at=now(),raw_payload=EXCLUDED.raw_payload
                """,
            (
                reading_id,
                installation_id,
                collector_id,
                pv_input_id,
                captured_at,
                metrics.get("power_ac_w"),
                metrics.get("energy_today_kwh"),
                metrics.get("energy_total_kwh"),
                metrics.get("voltage_v"),
                metrics.get("current_a"),
                metrics.get("power_dc_w"),
                metrics.get("frequency_hz"),
                metrics.get("temperature_c"),
                metrics.get("status", "online"),
                metrics.get("quality", "valid"),
                metrics.get("source", "local_deye"),
                sync_state,
                raw_payload,
            ),
        )
        if sync_state == "pending":
            connection.execute(
                "INSERT INTO sync_outbox(reading_id) VALUES (%s) ON CONFLICT DO NOTHING", (reading_id,)
            )


def summary(db: Database, installation_id: str | None = None) -> dict[str, Any]:
    installation_row = installation(db)
    if not installation_row:
        return {
            "configured": False,
            "collectors": 0,
            "enabled_pv": 0,
            "power_ac_w": None,
            "energy_today_kwh": None,
            "energy_total_kwh": None,
            "pending_records": 0,
        }
    iid = installation_id or installation_row["id"]
    latest = db.fetch_one(
        """
        SELECT COALESCE(sum(power_ac_w) FILTER (WHERE pv_input_id IS NULL),0) AS power_ac_w,
               COALESCE(sum(energy_today_kwh) FILTER (WHERE pv_input_id IS NULL),0) AS energy_today_kwh,
               COALESCE(sum(energy_total_kwh) FILTER (WHERE pv_input_id IS NULL),0) AS energy_total_kwh,
               max(captured_at) AS latest_at
        FROM readings WHERE installation_id=%s AND captured_at > now()-interval '10 minutes'
        """,
        (iid,),
    ) or {}
    counts = db.fetch_one(
        """
        SELECT (SELECT count(*) FROM collectors WHERE installation_id=%s AND enabled) AS collectors,
               (SELECT count(*) FROM pv_inputs p JOIN collectors c ON c.id=p.collector_id
                 WHERE c.installation_id=%s AND p.enabled) AS enabled_pv,
               (SELECT count(*) FROM sync_outbox o JOIN readings r ON r.reading_id=o.reading_id
                 WHERE r.installation_id=%s AND o.acked_at IS NULL) AS pending_records,
               (SELECT count(*) FROM alerts WHERE installation_id=%s AND status='active') AS active_alerts
        """,
        (iid, iid, iid, iid),
    ) or {}
    return {
        "configured": True,
        **{key: value for key, value in serialize(latest).items()},
        **counts,
    }


def readings(
    db: Database,
    *,
    collector_id: str | None = None,
    pv_input_id: str | None = None,
    since_hours: int = 24,
    limit: int = 500,
) -> list[dict[str, Any]]:
    clauses = ["r.captured_at >= now()-(%s * interval '1 hour')"]
    params: list[Any] = [max(1, min(24 * 31, since_hours))]
    if collector_id:
        clauses.append("r.collector_id=%s")
        params.append(collector_id)
    if pv_input_id:
        clauses.append("r.pv_input_id=%s")
        params.append(pv_input_id)
    params.append(max(1, min(5000, limit)))
    query = f"""
        SELECT r.*, c.name AS collector_name, p.channel, p.name AS pv_name
        FROM readings r JOIN collectors c ON c.id=r.collector_id
        LEFT JOIN pv_inputs p ON p.id=r.pv_input_id
        WHERE {' AND '.join(clauses)} ORDER BY r.captured_at DESC LIMIT %s
    """
    return [serialize(row) for row in db.fetch_all(query, params)]


def alerts(db: Database, status: str | None = None) -> list[dict[str, Any]]:
    if status:
        rows = db.fetch_all("SELECT * FROM alerts WHERE status=%s ORDER BY opened_at DESC LIMIT 300", (status,))
    else:
        rows = db.fetch_all("SELECT * FROM alerts ORDER BY opened_at DESC LIMIT 300")
    return [serialize(row) for row in rows]


def diagnostics(db: Database) -> dict[str, Any]:
    db_state = db.fetch_one("SELECT current_database() AS database, pg_size_pretty(pg_database_size(current_database())) AS size") or {}
    pending = db.fetch_one("SELECT count(*) AS count, min(r.captured_at) AS oldest FROM sync_outbox o JOIN readings r ON r.reading_id=o.reading_id WHERE o.acked_at IS NULL") or {}
    return {"database": db_state, "pending": serialize(pending), "collectors": collectors(db)}


def apply_retention(db: Database, days: int) -> int:
    cutoff = now_utc() - timedelta(days=max(1, days))
    with db.connection() as connection, connection.transaction():
        result = connection.execute(
                """
                DELETE FROM readings r WHERE r.captured_at < %s
                  AND r.sync_state IN ('synced','local_only')
                  AND NOT EXISTS (SELECT 1 FROM sync_outbox o WHERE o.reading_id=r.reading_id AND o.acked_at IS NULL)
                """,
                (cutoff,),
        )
        return result.rowcount


def pending_batch(db: Database, limit: int = 200) -> list[dict[str, Any]]:
    return [
        serialize(row)
        for row in db.fetch_all(
            """
            SELECT r.* FROM readings r JOIN sync_outbox o ON o.reading_id=r.reading_id
            WHERE o.acked_at IS NULL AND o.next_attempt_at <= now()
            ORDER BY r.captured_at, r.reading_id LIMIT %s
            """,
            (max(1, min(1000, limit)),),
        )
    ]


def mark_batch_attempt(db: Database, reading_ids: list[str], error: str | None = None) -> None:
    if not reading_ids:
        return
    with db.connection() as connection, connection.transaction():
        for reading_id in reading_ids:
            if error:
                connection.execute(
                        """
                        UPDATE sync_outbox SET attempts=attempts+1,last_attempt_at=now(),last_error=%s,
                          next_attempt_at=now()+least(interval '1 hour', power(2, least(attempts,8))*interval '5 seconds')
                        WHERE reading_id=%s
                        """,
                        (error[:500], reading_id),
                )
            else:
                connection.execute(
                    "UPDATE sync_outbox SET last_attempt_at=now(),last_error=NULL WHERE reading_id=%s",
                    (reading_id,),
                )


def mark_batch_ack(db: Database, reading_ids: list[str]) -> None:
    if not reading_ids:
        return
    with db.connection() as connection, connection.transaction():
        for reading_id in reading_ids:
            connection.execute(
                    "UPDATE sync_outbox SET acked_at=now(),last_attempt_at=now(),last_error=NULL WHERE reading_id=%s",
                    (reading_id,),
            )
            connection.execute(
                "UPDATE readings SET sync_state='synced',synced_at=now() WHERE reading_id=%s",
                (reading_id,),
            )


def csv_report(rows: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    fields = [
        "captured_at", "collector_name", "pv_name", "power_ac_w", "power_dc_w",
        "voltage_v", "current_a", "energy_today_kwh", "energy_total_kwh", "quality", "source",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
