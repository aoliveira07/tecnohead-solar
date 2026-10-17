-- Runtime migrations validate and quote SOLAR_DB_SCHEMA. This file documents
-- the default schema and is also usable manually with schema=solar.
CREATE SCHEMA IF NOT EXISTS solar;
-- The API creates the remaining tables idempotently at service start.

