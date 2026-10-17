import uuid
from datetime import UTC, datetime
from decimal import Decimal

from tecnohead_solar.store import READING_INSERT_SQL, serialize, summary


def test_reading_insert_sql_matches_reading_parameters() -> None:
    assert READING_INSERT_SQL.count("%s") == 18


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


def test_summary_uses_one_latest_ac_sample_per_collector() -> None:
    installation_id = uuid.uuid4()

    class FakeDatabase:
        def __init__(self) -> None:
            self.queries: list[str] = []

        def fetch_one(self, sql: str, params: tuple = ()) -> dict:
            self.queries.append(sql)
            if "FROM installations" in sql:
                return {"id": installation_id}
            if "latest_per_collector" in sql:
                return {
                    "power_ac_w": Decimal(7500),
                    "energy_today_kwh": Decimal("25.6"),
                    "energy_total_kwh": Decimal(40000),
                    "latest_at": datetime(2026, 1, 1, tzinfo=UTC),
                }
            return {"collectors": 5, "enabled_pv": 19, "pending_records": 0, "active_alerts": 0}

    database = FakeDatabase()

    result = summary(database)

    assert result["power_ac_w"] == 7500.0
    assert result["energy_today_kwh"] == 25.6
    assert any("DISTINCT ON (collector_id)" in query for query in database.queries)

