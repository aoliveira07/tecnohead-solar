"""Optional MQTT Discovery publisher."""

from __future__ import annotations

import json
import logging
from typing import Any

try:
    from aiomqtt import Client, MqttError
except ImportError:  # pragma: no cover - optional local test dependency
    Client = None

    class MqttError(Exception):
        pass


LOGGER = logging.getLogger("tecnohead_solar.mqtt")


def discovery_payload(installation_id: str, collector: dict[str, Any], channel: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    stable = f"tecnohead_solar_{installation_id}_{collector['logger_serial']}"
    if channel:
        stable = f"{stable}_pv{channel['channel']}"
        name = f"{collector['name']} PV{channel['channel']} potência"
        state_key = "power_dc_w"
        unit = "W"
        device_class = "power"
        state_class = "measurement"
    else:
        name = f"{collector['name']} potência AC"
        state_key = "power_ac_w"
        unit = "W"
        device_class = "power"
        state_class = "measurement"
    object_id = stable.replace("-", "_")
    topic = f"homeassistant/sensor/{object_id}/config"
    payload = {
        "unique_id": stable,
        "name": name,
        "state_topic": f"tecnohead_solar/{installation_id}/{collector['logger_serial']}/state",
        "value_template": f"{{{{ value_json.{state_key} }}}}",
        "unit_of_measurement": unit,
        "device_class": device_class,
        "state_class": state_class,
        "availability_topic": f"tecnohead_solar/{installation_id}/{collector['logger_serial']}/availability",
        "payload_available": "online",
        "payload_not_available": "offline",
        "device": {
            "identifiers": [f"tecnohead_solar_{collector['logger_serial']}"],
            "name": collector["name"],
            "manufacturer": "Deye",
            "model": "Microinverter / logger",
        },
    }
    return topic, payload


async def publish_discovery(settings: Any, installation_id: str, collector: dict[str, Any], channels: list[dict[str, Any]]) -> dict[str, Any]:
    if not settings.mqtt_enabled or not settings.mqtt_host or Client is None:
        return {"state": "disabled" if not settings.mqtt_enabled else "unavailable"}
    try:
        async with Client(
            hostname=settings.mqtt_host,
            port=settings.mqtt_port,
            username=settings.mqtt_username or None,
            password=settings.mqtt_password or None,
            identifier="tecnohead-solar",
        ) as client:
            base = f"tecnohead_solar/{installation_id}/{collector['logger_serial']}"
            await client.publish(f"{base}/availability", payload="online", retain=True)
            topic, payload = discovery_payload(installation_id, collector)
            await client.publish(topic, payload=json.dumps(payload), retain=True)
            for channel in channels:
                topic, payload = discovery_payload(installation_id, collector, channel)
                await client.publish(topic, payload=json.dumps(payload), retain=True)
        return {"state": "online"}
    except (MqttError, OSError) as exc:
        LOGGER.warning("MQTT publish failed: %s", type(exc).__name__)
        return {"state": "offline", "detail": type(exc).__name__}
