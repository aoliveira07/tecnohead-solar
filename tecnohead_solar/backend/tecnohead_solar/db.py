"""PostgreSQL persistence for the local App.

The connection is a Unix socket inside the App container. No PostgreSQL port
is exposed to the LAN and the Home Assistant Recorder is never touched.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from contextlib import contextmanager
from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS installations (
    id uuid PRIMARY KEY,
    name text NOT NULL,
    timezone text NOT NULL DEFAULT 'UTC',
    latitude double precision,
    longitude double precision,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS collectors (
    id uuid PRIMARY KEY,
    installation_id uuid NOT NULL REFERENCES installations(id) ON DELETE CASCADE,
    name text NOT NULL,
    ip inet NOT NULL,
    port integer NOT NULL DEFAULT 8899,
    logger_serial bigint NOT NULL,
    inverter_serial text,
    profile text NOT NULL DEFAULT 'deye_micro_v1',
    slave_id integer NOT NULL DEFAULT 1,
    enabled boolean NOT NULL DEFAULT true,
    last_seen_at timestamptz,
    last_status text NOT NULL DEFAULT 'never_tested',
    last_error text,
    last_payload jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (installation_id, logger_serial)
);

CREATE TABLE IF NOT EXISTS pv_inputs (
    id uuid PRIMARY KEY,
    collector_id uuid NOT NULL REFERENCES collectors(id) ON DELETE CASCADE,
    channel integer NOT NULL CHECK (channel BETWEEN 1 AND 4),
    name text NOT NULL,
    enabled boolean NOT NULL DEFAULT true,
    physical_location text,
    wp numeric(10,2),
    azimuth numeric(6,2),
    tilt numeric(6,2),
    shade_factor numeric(5,4) NOT NULL DEFAULT 1,
    map_x numeric(7,3),
    map_y numeric(7,3),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (collector_id, channel)
);

CREATE TABLE IF NOT EXISTS readings (
    reading_id uuid PRIMARY KEY,
    installation_id uuid NOT NULL REFERENCES installations(id) ON DELETE CASCADE,
    collector_id uuid NOT NULL REFERENCES collectors(id) ON DELETE CASCADE,
    pv_input_id uuid REFERENCES pv_inputs(id) ON DELETE SET NULL,
    captured_at timestamptz NOT NULL,
    received_at timestamptz NOT NULL DEFAULT now(),
    power_ac_w numeric(12,3),
    energy_today_kwh numeric(12,4),
    energy_total_kwh numeric(14,4),
    voltage_v numeric(10,3),
    current_a numeric(10,3),
    power_dc_w numeric(12,3),
    frequency_hz numeric(8,3),
    temperature_c numeric(8,3),
    status_code integer,
    status text NOT NULL DEFAULT 'online',
    quality text NOT NULL DEFAULT 'valid',
    source text NOT NULL DEFAULT 'local_deye',
    sync_state text NOT NULL DEFAULT 'pending',
    synced_at timestamptz,
    raw_payload jsonb
);

CREATE TABLE IF NOT EXISTS sync_outbox (
    reading_id uuid PRIMARY KEY REFERENCES readings(reading_id) ON DELETE CASCADE,
    attempts integer NOT NULL DEFAULT 0,
    next_attempt_at timestamptz NOT NULL DEFAULT now(),
    last_attempt_at timestamptz,
    last_error text,
    acked_at timestamptz
);

CREATE TABLE IF NOT EXISTS alerts (
    id uuid PRIMARY KEY,
    installation_id uuid NOT NULL REFERENCES installations(id) ON DELETE CASCADE,
    collector_id uuid REFERENCES collectors(id) ON DELETE SET NULL,
    pv_input_id uuid REFERENCES pv_inputs(id) ON DELETE SET NULL,
    code text NOT NULL,
    severity text NOT NULL,
    status text NOT NULL DEFAULT 'active',
    title text NOT NULL,
    detail text NOT NULL,
    opened_at timestamptz NOT NULL DEFAULT now(),
    acknowledged_at timestamptz,
    resolved_at timestamptz,
    context jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (installation_id, collector_id, pv_input_id, code, status)
);

CREATE TABLE IF NOT EXISTS app_settings (
    key text PRIMARY KEY,
    value jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_readings_captured_at ON readings (captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_readings_collector_time ON readings (collector_id, captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_readings_pv_time ON readings (pv_input_id, captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_readings_sync ON readings (sync_state, captured_at);
CREATE INDEX IF NOT EXISTS idx_outbox_next_attempt ON sync_outbox (next_attempt_at, attempts);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts (status, opened_at DESC);
"""


def _json(value: Any) -> Any:
    return Jsonb(value) if isinstance(value, (dict, list)) else value


class Database:
    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or os.getenv(
            "SOLAR_DATABASE_URL",
            "host=/run/tecnohead-solar port=55432 dbname=tecnohead_solar user=solar_app",
        )
        self.pool = ConnectionPool(
            conninfo=self.dsn,
            min_size=1,
            max_size=8,
            kwargs={"row_factory": dict_row, "application_name": "tecnohead_solar"},
            open=False,
        )

    def open(self) -> None:
        self.pool.open(wait=True)

    def close(self) -> None:
        self.pool.close()

    @contextmanager
    def connection(self):
        with self.pool.connection() as connection:
            yield connection

    def ensure_schema(self) -> None:
        with self.connection() as connection, connection.transaction():
            connection.execute(SCHEMA_SQL)
            connection.execute(
                "INSERT INTO schema_migrations(version) VALUES (%s) ON CONFLICT DO NOTHING",
                ("0001_initial",),
            )

    def fetch_one(self, sql: str, params: Sequence[Any] = ()) -> dict[str, Any] | None:
        with self.connection() as connection:
            return connection.execute(sql, tuple(_json(v) for v in params)).fetchone()

    def fetch_all(self, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        with self.connection() as connection:
            return list(connection.execute(sql, tuple(_json(v) for v in params)).fetchall())

    def execute(self, sql: str, params: Sequence[Any] = ()) -> None:
        with self.connection() as connection, connection.transaction():
            connection.execute(sql, tuple(_json(v) for v in params))

    def executemany(self, sql: str, params: Iterable[Sequence[Any]]) -> None:
        with self.connection() as connection, connection.transaction():
            connection.executemany(sql, [tuple(_json(v) for v in row) for row in params])
