"""Background collector, retention, MQTT and API-sync worker."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .alerts import evaluate_collector, upsert_active_alerts
from .db import Database
from .driver import read_collector_async
from .mqtt import publish_discovery
from .settings import Settings
from .store import apply_retention, collectors, installation, save_collector_probe, save_reading
from .sync import sync_once

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
LOGGER = logging.getLogger("tecnohead_solar.worker")


async def collect_one(db: Database, settings: Settings, collector: dict[str, Any]) -> None:
    installation_row = installation(db)
    if not installation_row:
        return
    try:
        result = await read_collector_async(
            address=str(collector["ip"]),
            logger_serial=int(collector["logger_serial"]),
            port=int(collector["port"]),
            slave_id=int(collector["slave_id"]),
            timeout=8,
        )
        save_collector_probe(db, str(collector["id"]), "online", result.as_payload())
        pv_rows = db.fetch_all("SELECT * FROM pv_inputs WHERE collector_id=%s ORDER BY channel", (collector["id"],))
        sync_state = "pending" if settings.api_enabled and settings.api_url and settings.api_token else "local_only"
        # Use the same stable ID scheme as the interactive probe without
        # calling the HTTP layer.
        import uuid

        ac_id = uuid.uuid5(uuid.NAMESPACE_URL, f"tecnohead-solar:{collector['logger_serial']}:{result.captured_at.isoformat()}:ac")
        save_reading(
            db,
            reading_id=ac_id,
            installation_id=str(installation_row["id"]),
            collector_id=str(collector["id"]),
            pv_input_id=None,
            captured_at=result.captured_at,
            metrics={
                "power_ac_w": result.power_ac_w,
                "energy_today_kwh": result.energy_today_kwh,
                "energy_total_kwh": result.energy_total_kwh,
                "frequency_hz": result.frequency_hz,
                "status": "online",
                "quality": "valid",
            },
            raw_payload=result.as_payload(),
            sync_state=sync_state,
        )
        candidates = []
        for channel in result.channels:
            pv_row = next((row for row in pv_rows if row["channel"] == channel.channel), None)
            if not pv_row or not pv_row["enabled"]:
                continue
            import uuid

            reading_id = uuid.uuid5(uuid.NAMESPACE_URL, f"tecnohead-solar:{collector['logger_serial']}:{result.captured_at.isoformat()}:pv{channel.channel}")
            metrics = {
                "voltage_v": channel.voltage_v,
                "current_a": channel.current_a,
                "power_dc_w": channel.power_dc_w,
                "energy_today_kwh": channel.energy_today_kwh,
                "energy_total_kwh": channel.energy_total_kwh,
                "status": "online",
                "quality": channel.quality,
            }
            save_reading(
                db,
                reading_id=reading_id,
                installation_id=str(installation_row["id"]),
                collector_id=str(collector["id"]),
                pv_input_id=str(pv_row["id"]),
                captured_at=result.captured_at,
                metrics=metrics,
                raw_payload={"channel": channel.channel, **metrics},
                sync_state=sync_state,
            )
            candidates.extend(
                evaluate_collector(
                    db,
                    str(installation_row["id"]),
                    str(collector["id"]),
                    {"channels": [{**metrics, "channel": channel.channel, "pv_input_id": str(pv_row["id"]),}]},
                )
            )
        upsert_active_alerts(db, candidates)
        await publish_discovery(settings, str(installation_row["id"]), collector, [dict(row) for row in pv_rows if row["enabled"]])
    except Exception as exc:
        save_collector_probe(db, str(collector["id"]), "offline", {}, type(exc).__name__)
        LOGGER.warning("collector %s failed: %s: %s", collector["name"], type(exc).__name__, exc, exc_info=True)


async def run() -> None:
    db = Database()
    db.open()
    db.ensure_schema()
    last_retention = 0.0
    try:
        while True:
            settings = Settings.load()
            devices = [item for item in collectors(db) if item["enabled"]]
            for device in devices:
                await collect_one(db, settings, device)
            if settings.api_enabled:
                runtime_state = await sync_once(db, settings.api_url, settings.api_token, settings.ensure_installation_id())
            else:
                runtime_state = {"state": "disabled", "sent": 0}
            db.execute("INSERT INTO app_settings(key,value) VALUES ('last_sync',%s) ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value,updated_at=now()", (runtime_state,))
            if asyncio.get_running_loop().time() - last_retention > 3600:
                apply_retention(db, settings.retention_days)
                last_retention = asyncio.get_running_loop().time()
            await asyncio.sleep(settings.poll_interval)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run())
