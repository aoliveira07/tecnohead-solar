"""Offline clear-sky potential estimate.

This deliberately stays a transparent local model. It is not a weather
forecast and is labelled as theoretical in the UI and reports.
"""

from __future__ import annotations

import math
from datetime import UTC, date, datetime
from typing import Any


def _solar_declination(day_of_year: int) -> float:
    return math.radians(23.44) * math.sin(math.radians(360 * (284 + day_of_year) / 365))


def _sun_altitude(latitude: float, longitude: float, when: datetime) -> float:
    day = when.timetuple().tm_yday
    declination = _solar_declination(day)
    # UTC solar time is sufficient for a labelled theoretical estimate. The
    # longitude term accounts for the local meridian without a weather source.
    utc_hour = when.hour + when.minute / 60 + when.second / 3600
    solar_hour = utc_hour + longitude / 15
    hour_angle = math.radians(15 * (solar_hour - 12))
    latitude_rad = math.radians(latitude)
    return math.degrees(
        math.asin(
            math.sin(latitude_rad) * math.sin(declination)
            + math.cos(latitude_rad) * math.cos(declination) * math.cos(hour_angle)
        )
    )


def theoretical_forecast(
    *,
    latitude: float | None,
    longitude: float | None,
    panels: list[dict[str, Any]],
    when: datetime | None = None,
) -> dict[str, Any]:
    now = (when or datetime.now(UTC)).astimezone(UTC)
    if latitude is None or longitude is None:
        return {
            "kind": "theoretical_clear_sky",
            "available": False,
            "label": "Configure latitude e longitude para calcular o potencial teórico.",
            "date": date.today().isoformat(),
            "watts": None,
        }
    altitude = _sun_altitude(latitude, longitude, now)
    sun_factor = max(0.0, math.sin(math.radians(max(0.0, altitude))))
    total_wp = 0.0
    adjusted_wp = 0.0
    for panel in panels:
        if not panel.get("enabled"):
            continue
        try:
            wp = float(panel.get("wp") or 0)
        except (TypeError, ValueError):
            wp = 0
        try:
            shade = max(0.0, min(1.0, float(panel.get("shade_factor") or 1)))
        except (TypeError, ValueError):
            shade = 1
        total_wp += wp
        adjusted_wp += wp * shade
    watts = round(adjusted_wp * sun_factor, 2) if adjusted_wp else None
    return {
        "kind": "theoretical_clear_sky",
        "available": bool(total_wp),
        "label": "Potencial teórico de céu limpo; não é previsão meteorológica.",
        "date": now.date().isoformat(),
        "sun_altitude_deg": round(altitude, 2),
        "sun_factor": round(sun_factor, 4),
        "installed_wp": round(total_wp, 2),
        "adjusted_wp": round(adjusted_wp, 2),
        "watts": watts,
        "source": "local_solar_geometry",
    }
