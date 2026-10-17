from datetime import UTC, datetime

from tecnohead_solar.forecast import theoretical_forecast


def test_theoretical_forecast_is_explicitly_local_and_not_weather() -> None:
    result = theoretical_forecast(
        latitude=-23.5,
        longitude=-46.6,
        panels=[{"enabled": True, "wp": 550, "shade_factor": 0.9}],
        when=datetime(2026, 1, 15, 16, tzinfo=UTC),
    )

    assert result["kind"] == "theoretical_clear_sky"
    assert result["source"] == "local_solar_geometry"
    assert result["adjusted_wp"] == 495.0
    assert "não é previsão meteorológica" in result["label"]


def test_forecast_without_location_is_unavailable() -> None:
    result = theoretical_forecast(latitude=None, longitude=None, panels=[])

    assert result["available"] is False
    assert result["watts"] is None

