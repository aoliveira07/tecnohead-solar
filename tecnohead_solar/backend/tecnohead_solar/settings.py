"""Runtime settings loaded from Supervisor options and private App data."""

from __future__ import annotations

import json
import os
import secrets
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.getenv("SOLAR_DATA_DIR", "/data/tecnohead_solar"))
OPTIONS_PATH = Path(os.getenv("SOLAR_OPTIONS_PATH", "/data/options.json"))
PRIVATE_SETTINGS_PATH = DATA_DIR / "settings.json"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value) if value is not None else default


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float | None, minimum: float, maximum: float) -> float | None:
    try:
        candidate = float(value)
    except (TypeError, ValueError):
        return default
    return candidate if minimum <= candidate <= maximum else default


@dataclass(slots=True)
class Settings:
    """Effective App settings.

    Secrets are intentionally represented in memory only. ``public`` never
    serializes API or MQTT passwords.
    """

    data_dir: Path = DATA_DIR
    version: str = os.getenv("APP_VERSION", "0.1.7")
    log_level: str = "info"
    poll_interval: int = 60
    retention_days: int = 7
    api_enabled: bool = False
    api_url: str = ""
    api_token: str = ""
    mqtt_enabled: bool = True
    mqtt_host: str = ""
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    timezone: str = "UTC"
    latitude: float | None = None
    longitude: float | None = None
    installation_id: str = ""

    @classmethod
    def load(cls) -> Settings:
        options = _read_json(OPTIONS_PATH)
        private = _read_json(PRIVATE_SETTINGS_PATH)
        merged: dict[str, Any] = {**options, **private}
        if os.getenv("TECNOHEAD_SOLAR_OPTIONS"):
            try:
                merged.update(json.loads(os.environ["TECNOHEAD_SOLAR_OPTIONS"]))
            except ValueError:
                pass

        settings = cls(
            log_level=str(merged.get("log_level", "info")).lower(),
            poll_interval=max(15, min(900, _as_int(merged.get("poll_interval"), 60))),
            retention_days=max(1, min(30, _as_int(merged.get("retention_days"), 7))),
            api_enabled=_as_bool(merged.get("api_enabled"), False),
            api_url=str(merged.get("api_url") or "").strip().rstrip("/"),
            api_token=str(merged.get("api_token") or ""),
            mqtt_enabled=_as_bool(merged.get("mqtt_enabled"), True),
            mqtt_host=str(merged.get("mqtt_host") or os.getenv("MQTT_HOST") or "").strip(),
            mqtt_port=max(1, min(65535, _as_int(merged.get("mqtt_port") or os.getenv("MQTT_PORT"), 1883))),
            mqtt_username=str(merged.get("mqtt_username") or os.getenv("MQTT_USERNAME") or ""),
            mqtt_password=str(merged.get("mqtt_password") or os.getenv("MQTT_PASSWORD") or ""),
            timezone=str(merged.get("timezone") or os.getenv("TZ") or "UTC"),
            latitude=_as_float(merged.get("latitude"), None, -90, 90),
            longitude=_as_float(merged.get("longitude"), None, -180, 180),
            installation_id=str(merged.get("installation_id") or ""),
        )
        return settings

    def public(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["data_dir"] = str(self.data_dir)
        payload["api_token_configured"] = bool(self.api_token)
        payload["mqtt_password_configured"] = bool(self.mqtt_password)
        payload.pop("api_token", None)
        payload.pop("mqtt_password", None)
        return payload

    def save_private(self, values: dict[str, Any]) -> None:
        """Merge UI settings into a 0600 private file without logging values."""

        self.data_dir.mkdir(parents=True, exist_ok=True)
        current = _read_json(PRIVATE_SETTINGS_PATH)
        current.update(values)
        temporary = PRIVATE_SETTINGS_PATH.with_suffix(".tmp")
        temporary.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
        os.chmod(temporary, 0o600)
        temporary.replace(PRIVATE_SETTINGS_PATH)

    def ensure_installation_id(self) -> str:
        if self.installation_id:
            return self.installation_id
        generated = secrets.token_hex(16)
        self.save_private({"installation_id": generated})
        self.installation_id = generated
        return generated
