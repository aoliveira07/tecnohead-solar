#!/usr/bin/env bash
set -Eeuo pipefail
: "${SOLAR_DATABASE_URL:?Defina SOLAR_DATABASE_URL}"
SCHEMA="${SOLAR_DB_SCHEMA:-solar}"
BACKUP_DIR="${SOLAR_BACKUP_DIR:-$PWD/backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "${BACKUP_DIR}"
OUTPUT="${BACKUP_DIR}/tecnohead-solar-${SCHEMA}-${STAMP}.dump"
pg_dump --format=custom --no-owner --schema="${SCHEMA}" --file="${OUTPUT}" "${SOLAR_DATABASE_URL}"
chmod 0600 "${OUTPUT}"
printf 'Backup criado: %s\n' "${OUTPUT}"

