import pytest
from tecnohead_solar_server.settings import safe_identifier


def test_schema_identifier_is_constrained() -> None:
    assert safe_identifier("Solar_2026") == "solar_2026"

    with pytest.raises(ValueError):
        safe_identifier("solar;drop schema public")

