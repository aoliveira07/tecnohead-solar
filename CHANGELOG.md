# Changelog

All notable changes to TecnoHead Solar are documented here.

## 0.1.9 — Corrected micro PV total-energy offsets

- Corrected the Deye micro register map for PV3/PV4 accumulated energy, which are separated from PV1/PV2 by the AC voltage register at address 73.
- Added a regression assertion covering all four channel total-energy offsets.

## 0.1.8 — Reading insert parameter count

- Match the PostgreSQL readings insert placeholders to its 18 parameters.
- Add a regression test for the insert statement shape.

## 0.1.7 — Runtime version and diagnostic evidence

- Keep the API/UI version aligned with the App manifest and image tag.
- Include the database exception detail and traceback in diagnostic logs for real field troubleshooting.

## 0.1.6 — JSONB collector probe persistence fix

- Serialize the collector probe payload as PostgreSQL JSONB so physical diagnostics and the background worker can persist successful Deye reads.

## 0.1.5 — JSONB reading persistence fix

- Adapt local reading payloads as PostgreSQL JSONB before insertion.

## 0.1.4 — HAOS Ingress proxy compatibility

- Accept the supervisor bridge subnet used by the HAOS Ingress proxy.

## 0.1.3 — HAOS runtime paths and PostgreSQL socket fix

- Align the container frontend/logo paths with the backend runtime layout.
- Allow the `solarapp` service user to traverse the private PostgreSQL socket directory.

## 0.1.2 — HAOS startup fix

- Set the service working directory explicitly so the web and collector processes import the bundled package on HAOS.

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
