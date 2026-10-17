import uuid
from datetime import UTC, datetime
from decimal import Decimal

from tecnohead_solar.store import serialize


def test_serialize_makes_database_rows_json_safe() -> None:
    identifier = uuid.uuid4()
    result = serialize(
        {
            "id": identifier,
            "value": Decimal("12.34"),
            "captured_at": datetime(2026, 1, 1, tzinfo=UTC),
            "nested": {"values": [Decimal("1.2"), identifier]},
        }
    )

    assert result["id"] == str(identifier)
    assert result["value"] == 12.34
    assert result["nested"]["values"] == [1.2, str(identifier)]

