from tecnohead_solar_server.db import schema_sql


def test_schema_sql_is_isolated_and_idempotent() -> None:
    sql = schema_sql("solar_client")

    assert 'CREATE SCHEMA IF NOT EXISTS "solar_client"' in sql
    assert 'CREATE TABLE IF NOT EXISTS "solar_client".readings' in sql
    assert "CREATE SCHEMA IF NOT EXISTS public" not in sql

