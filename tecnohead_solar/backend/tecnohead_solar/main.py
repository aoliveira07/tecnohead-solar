"""FastAPI web interface served through Home Assistant Ingress."""

from __future__ import annotations

import ipaddress
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from .db import Database
from .driver import read_collector_async
from .forecast import theoretical_forecast
from .reports import pdf_report
from .settings import Settings
from .store import (
    alerts,
    apply_retention,
    collector_detail,
    collectors,
    csv_report,
    diagnostics,
    installation,
    pv_inputs,
    readings,
    save_collector_probe,
    save_reading,
    setup_installation,
    summary,
)
from .sync import health_check, remote_history

LOGGER = logging.getLogger("tecnohead_solar.web")
BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"
INGRESS_PROXY_NETWORK = ipaddress.ip_network("172.30.32.0/24")

settings = Settings.load()
db = Database()
runtime: dict[str, Any] = {"api": {"state": "disabled"}, "mqtt": {"state": "unknown"}}


class PVInputPayload(BaseModel):
    channel: int = Field(ge=1, le=4)
    name: str = "PV"
    enabled: bool = True
    physical_location: str | None = None
    wp: float | None = Field(default=None, ge=0, le=20000)
    azimuth: float | None = Field(default=None, ge=0, le=360)
    tilt: float | None = Field(default=None, ge=0, le=90)
    shade_factor: float = Field(default=1, ge=0, le=1)
    map_x: float = 0
    map_y: float = 0


class CollectorPayload(BaseModel):
    id: str | None = None
    name: str
    ip: str
    port: int = Field(default=8899, ge=1, le=65535)
    logger_serial: int = Field(gt=0)
    inverter_serial: str | None = None
    profile: str = "deye_micro_v1"
    slave_id: int = Field(default=1, ge=1, le=247)
    enabled: bool = True
    pv_inputs: list[PVInputPayload] = Field(default_factory=list)

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, value: str) -> str:
        import ipaddress

        ipaddress.ip_address(value)
        return value


class SetupPayload(BaseModel):
    installation_id: str | None = None
    name: str = "Minha instalação solar"
    timezone: str = "UTC"
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    collectors: list[CollectorPayload] = Field(default_factory=list)


class APISettingsPayload(BaseModel):
    enabled: bool = False
    url: str = ""
    token: str = ""


class MQTTSettingsPayload(BaseModel):
    enabled: bool = True
    host: str = ""
    port: int = Field(default=1883, ge=1, le=65535)
    username: str = ""
    password: str = ""


async def _sync_state(current: Settings | None = None) -> dict[str, Any]:
    current = current or _effective_settings()
    if current.api_enabled:
        runtime["api"] = await health_check(current.api_url, current.api_token)
    else:
        runtime["api"] = {"state": "disabled", "detail": "API externa desabilitada"}
    return {
        "state": runtime.get("api", {}).get("state", "disabled"),
        "pending_records": summary(db).get("pending_records", 0),
        "last_detail": runtime.get("api", {}).get("detail"),
    }


def _effective_settings() -> Settings:
    global settings
    settings = Settings.load()
    return settings


def _ingress_guard(request: Request) -> JSONResponse | None:
    if request.url.path == "/health":
        return None
    if request.app.state.dev_mode:
        return None
    client_host = request.client.host if request.client else ""
    try:
        client_ip = ipaddress.ip_address(client_host)
    except ValueError:
        client_ip = None
    allowed = client_ip in INGRESS_PROXY_NETWORK if client_ip else False
    allowed = allowed or client_host in {"127.0.0.1", "::1"}
    if not allowed:
        return JSONResponse(status_code=403, content={"detail": "Ingress only"})
    return None


@asynccontextmanager
async def lifespan(application: FastAPI):
    global settings
    settings = Settings.load()
    db.open()
    db.ensure_schema()
    settings.ensure_installation_id()
    application.state.dev_mode = False
    LOGGER.info("TecnoHead Solar %s started with private PostgreSQL", settings.version)
    yield
    db.close()


app = FastAPI(title="TecnoHead Solar", version="0.1.4", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Ingress-Path"],
)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")


@app.middleware("http")
async def ingress_only(request: Request, call_next):
    blocked = _ingress_guard(request)
    if blocked:
        return blocked
    return await call_next(request)


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/logo.png", include_in_schema=False)
async def logo() -> FileResponse:
    return FileResponse(Path(__file__).resolve().parents[2] / "logo.png")


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, Any]:
    configured = installation(db) is not None
    return {
        "ok": True,
        "app": "tecnohead_solar",
        "version": settings.version,
        "database": "postgresql_local",
        "configured": configured,
        "api_state": runtime.get("api", {}).get("state", "disabled"),
    }


@app.get("/api/v1/status")
async def status() -> dict[str, Any]:
    current = _effective_settings()
    forecast = theoretical_forecast(
        latitude=current.latitude,
        longitude=current.longitude,
        panels=pv_inputs(db),
    )
    return {
        "app": {"name": "TecnoHead Solar", "version": current.version, "stage": "experimental"},
        "summary": summary(db),
        "collectors": collectors(db),
        "alerts": alerts(db, "active"),
        "api": await _sync_state(current),
        "mqtt": runtime.get("mqtt", {"state": "unknown"}),
        "forecast": forecast,
    }


@app.get("/api/v1/setup")
async def get_setup() -> dict[str, Any]:
    current = _effective_settings()
    return {
        "installation": installation(db),
        "collectors": collectors(db),
        "pv_inputs": pv_inputs(db),
        "settings": current.public(),
    }


@app.post("/api/v1/setup")
async def save_setup(payload: SetupPayload) -> dict[str, Any]:
    current = _effective_settings()
    if payload.installation_id:
        try:
            uuid.UUID(payload.installation_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="installation_id inválido") from exc
    saved = setup_installation(db, payload.model_dump())
    current.save_private(
        {
            "installation_id": saved["id"],
            "timezone": payload.timezone,
            "latitude": payload.latitude,
            "longitude": payload.longitude,
        }
    )
    return {"ok": True, "installation": saved, "collectors": collectors(db), "pv_inputs": pv_inputs(db)}


@app.get("/api/v1/collectors")
async def get_collectors() -> list[dict[str, Any]]:
    return collectors(db)


@app.get("/api/v1/collectors/{collector_id}")
async def get_collector(collector_id: str) -> dict[str, Any]:
    item = collector_detail(db, collector_id)
    if not item:
        raise HTTPException(status_code=404, detail="Coletor não encontrado")
    return item


async def _probe_collector(collector_id: str) -> dict[str, Any]:
    collector = db.fetch_one("SELECT * FROM collectors WHERE id=%s", (collector_id,))
    if not collector:
        raise HTTPException(status_code=404, detail="Coletor não encontrado")
    current = _effective_settings()
    try:
        result = await read_collector_async(
            address=str(collector["ip"]),
            logger_serial=int(collector["logger_serial"]),
            port=int(collector["port"]),
            slave_id=int(collector["slave_id"]),
            timeout=8,
        )
        save_collector_probe(db, collector_id, "online", result.as_payload())
        installation_row = installation(db)
        if not installation_row:
            raise HTTPException(status_code=409, detail="Conclua o assistente primeiro")
        pv_rows = db.fetch_all("SELECT * FROM pv_inputs WHERE collector_id=%s ORDER BY channel", (collector_id,))
        sync_state = "pending" if current.api_enabled and current.api_url and current.api_token else "local_only"
        ac_id = uuid.uuid5(uuid.NAMESPACE_URL, f"tecnohead-solar:{collector['logger_serial']}:{result.captured_at.isoformat()}:ac")
        save_reading(
            db,
            reading_id=ac_id,
            installation_id=str(installation_row["id"]),
            collector_id=collector_id,
            pv_input_id=None,
            captured_at=result.captured_at,
            metrics={
                "power_ac_w": result.power_ac_w,
                "energy_today_kwh": result.energy_today_kwh,
                "energy_total_kwh": result.energy_total_kwh,
                "frequency_hz": result.frequency_hz,
                "temperature_c": result.temperature_c,
                "status": "online",
                "quality": "valid",
            },
            raw_payload=result.as_payload(),
            sync_state=sync_state,
        )
        for channel in result.channels:
            pv_row = next((row for row in pv_rows if row["channel"] == channel.channel), None)
            if not pv_row or not pv_row["enabled"]:
                continue
            channel_payload = {
                "channel": channel.channel,
                "voltage_v": channel.voltage_v,
                "current_a": channel.current_a,
                "power_dc_w": channel.power_dc_w,
                "energy_today_kwh": channel.energy_today_kwh,
                "energy_total_kwh": channel.energy_total_kwh,
                "supported": channel.supported,
                "quality": channel.quality,
            }
            reading_id = uuid.uuid5(uuid.NAMESPACE_URL, f"tecnohead-solar:{collector['logger_serial']}:{result.captured_at.isoformat()}:pv{channel.channel}")
            save_reading(
                db,
                reading_id=reading_id,
                installation_id=str(installation_row["id"]),
                collector_id=collector_id,
                pv_input_id=str(pv_row["id"]),
                captured_at=result.captured_at,
                metrics={**channel_payload, "status": "online", "source": "local_deye"},
                raw_payload=channel_payload,
                sync_state=sync_state,
            )
        return {"ok": True, "collector": collector_detail(db, collector_id), "reading": result.as_payload()}
    except HTTPException:
        raise
    except Exception as exc:
        error = type(exc).__name__
        save_collector_probe(db, collector_id, "offline", {}, error)
        raise HTTPException(status_code=502, detail=f"Leitura Deye falhou: {error}") from exc


@app.post("/api/v1/collectors/{collector_id}/probe")
async def probe_collector(collector_id: str) -> dict[str, Any]:
    return await _probe_collector(collector_id)


@app.post("/api/v1/diagnostics/run")
async def run_diagnostics() -> dict[str, Any]:
    results = []
    for collector in collectors(db):
        if collector["enabled"]:
            try:
                results.append(await _probe_collector(str(collector["id"])))
            except HTTPException as exc:
                results.append({"ok": False, "collector_id": collector["id"], "status_code": exc.status_code, "detail": exc.detail})
    return {"ok": all(item.get("ok") for item in results) if results else False, "results": results}


@app.get("/api/v1/readings")
async def get_readings(
    collector_id: str | None = None,
    pv_input_id: str | None = None,
    since_hours: int = Query(default=24, ge=1, le=24 * 31),
    limit: int = Query(default=500, ge=1, le=5000),
) -> dict[str, Any]:
    current = _effective_settings()
    local_rows = readings(db, collector_id=collector_id, pv_input_id=pv_input_id, since_hours=since_hours, limit=limit)
    rows = list(local_rows)
    if current.api_enabled and current.api_url and current.api_token:
        local_ids = {str(row["reading_id"]) for row in local_rows if row.get("reading_id")}
        collector_map = {str(row["id"]): row for row in collectors(db)}
        pv_map = {str(row["id"]): row for row in pv_inputs(db)}
        for remote in await remote_history(current.api_url, current.api_token, since_hours, limit):
            reading_id = str(remote.get("reading_id", ""))
            if not reading_id or reading_id in local_ids:
                continue
            payload = remote.get("payload") if isinstance(remote.get("payload"), dict) else {}
            merged = {**payload, **remote, "source": "server_postgresql"}
            collector = collector_map.get(str(merged.get("collector_id")), {})
            pv = pv_map.get(str(merged.get("pv_input_id")), {})
            merged.setdefault("collector_name", collector.get("name", "Coletor remoto"))
            merged.setdefault("pv_name", pv.get("name", "AC"))
            rows.append(merged)
    rows.sort(key=lambda row: str(row.get("captured_at", "")), reverse=True)
    return {"source": "hybrid" if len(rows) > len(local_rows) else "local_postgresql", "rows": rows[:limit], "count": min(len(rows), limit), "period_hours": since_hours}


@app.get("/api/v1/forecast")
async def get_forecast() -> dict[str, Any]:
    current = _effective_settings()
    return theoretical_forecast(latitude=current.latitude, longitude=current.longitude, panels=pv_inputs(db))


@app.get("/api/v1/alerts")
async def get_alerts(status: str | None = None) -> list[dict[str, Any]]:
    return alerts(db, status)


@app.get("/api/v1/diagnostics")
async def get_diagnostics() -> dict[str, Any]:
    return diagnostics(db)


@app.get("/api/v1/settings")
async def get_settings() -> dict[str, Any]:
    current = _effective_settings()
    return {"settings": current.public(), "api": await _sync_state(current)}


@app.post("/api/v1/settings/api")
async def save_api_settings(payload: APISettingsPayload) -> dict[str, Any]:
    current = _effective_settings()
    values = {"api_enabled": payload.enabled, "api_url": payload.url.rstrip("/")}
    if payload.token:
        values["api_token"] = payload.token
    current.save_private(values)
    _effective_settings()
    return {"ok": True, "settings": settings.public(), "api": await _sync_state(_effective_settings())}


@app.post("/api/v1/settings/mqtt")
async def save_mqtt_settings(payload: MQTTSettingsPayload) -> dict[str, Any]:
    current = _effective_settings()
    values = {
        "mqtt_enabled": payload.enabled,
        "mqtt_host": payload.host,
        "mqtt_port": payload.port,
        "mqtt_username": payload.username,
    }
    if payload.password:
        values["mqtt_password"] = payload.password
    current.save_private(values)
    _effective_settings()
    return {"ok": True, "settings": settings.public()}


@app.post("/api/v1/settings/api/test")
async def test_api() -> dict[str, Any]:
    current = _effective_settings()
    return await _sync_state(current)


@app.post("/api/v1/maintenance/retention")
async def run_retention() -> dict[str, Any]:
    current = _effective_settings()
    return {"deleted": apply_retention(db, current.retention_days), "retention_days": current.retention_days}


@app.get("/api/v1/reports.csv")
async def report_csv(
    since_hours: int = Query(default=24, ge=1, le=24 * 31),
    limit: int = Query(default=2000, ge=1, le=5000),
) -> Response:
    current = _effective_settings()
    local_rows = readings(db, since_hours=since_hours, limit=limit)
    rows = local_rows
    if current.api_enabled and current.api_url and current.api_token:
        remote_rows = await remote_history(current.api_url, current.api_token, since_hours, limit)
        local_ids = {str(row["reading_id"]) for row in local_rows if row.get("reading_id")}
        rows = local_rows + [row for row in remote_rows if str(row.get("reading_id")) not in local_ids]
    return Response(content=csv_report(rows), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=tecnohead-solar.csv"})


@app.get("/api/v1/reports.pdf")
async def report_pdf(
    since_hours: int = Query(default=24, ge=1, le=24 * 31),
    limit: int = Query(default=500, ge=1, le=5000),
) -> Response:
    current = _effective_settings()
    local_rows = readings(db, since_hours=since_hours, limit=limit)
    rows = local_rows
    if current.api_enabled and current.api_url and current.api_token:
        remote_rows = await remote_history(current.api_url, current.api_token, since_hours, limit)
        local_ids = {str(row["reading_id"]) for row in local_rows if row.get("reading_id")}
        rows = local_rows + [row for row in remote_rows if str(row.get("reading_id")) not in local_ids]
    return Response(content=pdf_report(rows), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=tecnohead-solar.pdf"})
