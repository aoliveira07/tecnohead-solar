#!/usr/bin/env bash
set -Eeuo pipefail
: "${SOLAR_DATABASE_URL:?Defina SOLAR_DATABASE_URL}"
: "${SOLAR_API_TOKEN:?Defina SOLAR_API_TOKEN}"
PORT="${SOLAR_PORT:-18081}"
if command -v systemctl >/dev/null 2>&1; then
  systemctl --user --no-pager --full status "${SOLAR_SERVICE_NAME:-tecnohead-solar-api}.service" || true
fi
curl --fail --silent "http://127.0.0.1:${PORT}/api/v1/solar/health" \
  -H "Authorization: Bearer ${SOLAR_API_TOKEN}"
printf '\n'

