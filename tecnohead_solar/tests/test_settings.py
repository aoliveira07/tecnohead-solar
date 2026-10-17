import json

from tecnohead_solar import settings as settings_module


def test_settings_use_independent_longitude_bounds(tmp_path, monkeypatch) -> None:
    options = tmp_path / "options.json"
    private = tmp_path / "settings.json"
    options.write_text(json.dumps({"latitude": -23.5, "longitude": -120.25}), encoding="utf-8")
    monkeypatch.setattr(settings_module, "OPTIONS_PATH", options)
    monkeypatch.setattr(settings_module, "PRIVATE_SETTINGS_PATH", private)

    loaded = settings_module.Settings.load()

    assert loaded.latitude == -23.5
    assert loaded.longitude == -120.25


def test_settings_reject_out_of_range_coordinates(tmp_path, monkeypatch) -> None:
    options = tmp_path / "options.json"
    private = tmp_path / "settings.json"
    options.write_text(json.dumps({"latitude": 91, "longitude": 181}), encoding="utf-8")
    monkeypatch.setattr(settings_module, "OPTIONS_PATH", options)
    monkeypatch.setattr(settings_module, "PRIVATE_SETTINGS_PATH", private)

    loaded = settings_module.Settings.load()

    assert loaded.latitude is None
    assert loaded.longitude is None

