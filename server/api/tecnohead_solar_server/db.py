"""Small, schema-isolated PostgreSQL layer for the optional server API."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .settings import ServerSettings


def _q(identifier: str) -> str:
    return f'"{identifier}"'


def connect(settings: ServerSettings) -> psycopg.Connection[Any]:
    if not settings.database_url:
        raise RuntimeError("SOLAR_DATABASE_URL não configurada")
    return psycopg.connect(
        settings.database_url,
        row_factory=dict_row,
        application_name="tecnohead_solar_server",
    )


def schema_sql(schema: str) -> str:
    s = _q(schema)
    return f"""
CREATE SCHEMA IF NOT EXISTS {s};
CREATE TABLE IF NOT EXISTS {s}.installations (
    id uuid PRIMARY KEY,
    name text,
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS {s}.readings (
    reading_id uuid PRIMARY KEY,
    installation_id uuid NOT NULL,
    collector_id uuid,
    pv_input_id uuid,
    captured_at timestamptz NOT NULL,
    received_at timestamptz NOT NULL DEFAULT now(),
    payload jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS {s}.alerts (
    id uuid PRIMARY KEY,
    installation_id uuid NOT NULL,
    collector_id uuid,
    pv_input_id uuid,
    code text NOT NULL,
    severity text NOT NULL,
    status text NOT NULL,
    title text NOT NULL,
    detail text NOT NULL,
    opened_at timestamptz NOT NULL DEFAULT now(),
    payload jsonb NOT NULL DEFAULT '{{}}'::jsonb
);
CREATE INDEX IF NOT EXISTS {_q(f"{schema}_readings_time")} ON {s}.readings (captured_at DESC);
CREATE INDEX IF NOT EXISTS {_q(f"{schema}_readings_installation")} ON {s}.readings (installation_id, captured_at DESC);
CREATE INDEX IF NOT EXISTS {_q(f"{schema}_alerts_status")} ON {s}.alerts (status, opened_at DESC);
"""


def migrate(settings: ServerSettings) -> None:
    with connect(settings) as connection, connection.transaction():
        connection.execute(schema_sql(settings.db_schema))


def _uuid(value: Any) -> uuid.UUID | None:
    if value in (None, ""):
        return None
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _captured_at(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if value:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))  # noqa: FURB162
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return datetime.now(UTC)


def insert_batch(settings: ServerSettings, installation_id: str, rows: list[dict[str, Any]]) -> list[str]:
    acknowledged: list[str] = []
    schema = _q(settings.db_schema)
    installation_uuid = _uuid(installation_id)
    if installation_uuid is None:
        raise ValueError("installation_id inválido")
    with connect(settings) as connection, connection.transaction():
        connection.execute(
            f"INSERT INTO {schema}.installations(id,last_seen_at) VALUES (%s,now()) ON CONFLICT(id) DO UPDATE SET last_seen_at=now()",
            (installation_uuid,),
        )
        for row in rows:
            reading_uuid = _uuid(row.get("reading_id"))
            if reading_uuid is None:
                continue
            connection.execute(
                f"""
                    INSERT INTO {schema}.readings(reading_id,installation_id,collector_id,pv_input_id,captured_at,payload)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    ON CONFLICT(reading_id) DO NOTHING
                    """,
                (
                    reading_uuid,
                    installation_uuid,
                    _uuid(row.get("collector_id")),
                    _uuid(row.get("pv_input_id")),
                    _captured_at(row.get("captured_at")),
                    Jsonb(row),
                ),
            )
            acknowledged.append(str(reading_uuid))
    return acknowledged


def history(settings: ServerSettings, since_hours: int = 24, limit: int = 500) -> list[dict[str, Any]]:
    schema = _q(settings.db_schema)
    with connect(settings) as connection:
        return list(
            connection.execute(
                f"SELECT reading_id,installation_id,collector_id,pv_input_id,captured_at,received_at,payload FROM {schema}.readings WHERE captured_at >= now()-(%s * interval '1 hour') ORDER BY captured_at DESC LIMIT %s",
                (max(1, min(24 * 31, since_hours)), max(1, min(5000, limit))),
            ).fetchall()
        )


def summary(settings: ServerSettings) -> dict[str, Any]:
    schema = _q(settings.db_schema)
    with connect(settings) as connection:
        row = connection.execute(
            f"SELECT count(*)::int AS readings, max(captured_at) AS latest_at, count(*) FILTER (WHERE captured_at >= current_date)::int AS today FROM {schema}.readings"
        ).fetchone()
    return row or {"readings": 0, "latest_at": None, "today": 0}


def alerts(settings: ServerSettings) -> list[dict[str, Any]]:
    schema = _q(settings.db_schema)
    with connect(settings) as connection:
        return list(connection.execute(f"SELECT * FROM {schema}.alerts ORDER BY opened_at DESC LIMIT 300").fetchall())


def prune(settings: ServerSettings) -> int:
    schema = _q(settings.db_schema)
    with connect(settings) as connection, connection.transaction():
        result = connection.execute(
            f"DELETE FROM {schema}.readings WHERE captured_at < now() - (%s * interval '1 day')",
            (settings.retention_days,),
        )
        return result.rowcount

