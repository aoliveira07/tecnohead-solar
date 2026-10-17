# Changelog

All notable changes to TecnoHead Solar are documented here.

## 0.1.1 — experimental field build

- Hybrid history/report source: remote acknowledged readings plus local pending records without duplicate IDs.
- Hardened repeated setup saves, coordinate validation, JSON serialization and server schema isolation.
- Added remote alerts endpoint and expanded release validation/tests.

## 0.1.0 — experimental field build

- First independent Home Assistant OS App repository.
- Local Deye Solarman V5/TCP read-only driver with the Deye micro register profile.
- Persistent PostgreSQL cluster under `/data` with seven-day retention and a durable sync outbox.
- Responsive Ingress dashboard, schematic PV map, diagnostics, CSV/PDF reports and MQTT Discovery.
- Optional, isolated FastAPI/PostgreSQL server module with an idempotent installer.
- Release status remains `experimental` until the real HAOS and field homologation checklist is complete.
