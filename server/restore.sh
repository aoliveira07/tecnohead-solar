#!/usr/bin/env bash
set -Eeuo pipefail
: "${SOLAR_DATABASE_URL:?Defina SOLAR_DATABASE_URL}"
: "${SOLAR_BACKUP_FILE:?Defina SOLAR_BACKUP_FILE com o arquivo .dump}"
if [[ "${SOLAR_ALLOW_RESTORE:-}" != "YES" ]]; then
  printf '%s\n' "Restauração é destrutiva no schema selecionado. Defina SOLAR_ALLOW_RESTORE=YES para continuar." >&2
  exit 2
fi
SCHEMA="${SOLAR_DB_SCHEMA:-solar}"
pg_restore --clean --if-exists --no-owner --schema="${SCHEMA}" --dbname="${SOLAR_DATABASE_URL}" "${SOLAR_BACKUP_FILE}"
printf 'Restauração concluída no schema %s.\n' "${SCHEMA}"

