#!/usr/bin/env bash
set -Eeuo pipefail

# Reusable per-client installer. It never assumes a TecnoHead residence,
# database name, host, port or credential; all deployment identity is env-led.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${SOLAR_INSTALL_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/tecnohead-solar-server}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SERVICE_NAME="${SOLAR_SERVICE_NAME:-tecnohead-solar-api}"
PYTHON_BIN="${SOLAR_PYTHON:-python3}"
PORT="${SOLAR_PORT:-18081}"
BIND_HOST="${SOLAR_BIND_HOST:-127.0.0.1}"

if [[ "${1:-}" == "--check-only" ]]; then
  : "${SOLAR_DATABASE_URL:?Defina SOLAR_DATABASE_URL antes de instalar}"
  : "${SOLAR_API_TOKEN:?Defina SOLAR_API_TOKEN antes de instalar}"
  command -v "${PYTHON_BIN}" >/dev/null
  "${PYTHON_BIN}" -m venv --help >/dev/null
  printf '%s\n' "Pré-requisitos locais disponíveis; nenhuma alteração foi feita."
  exit 0
fi

: "${SOLAR_DATABASE_URL:?Defina SOLAR_DATABASE_URL antes de instalar}"
: "${SOLAR_API_TOKEN:?Defina SOLAR_API_TOKEN antes de instalar}"

quote_env() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  printf '"%s"' "$value"
}

mkdir -p "${INSTALL_DIR}" "${CONFIG_DIR}"
if [[ ! -d "${INSTALL_DIR}/.venv" ]]; then
  "${PYTHON_BIN}" -m venv "${INSTALL_DIR}/.venv"
fi

install -d "${INSTALL_DIR}/api"
rm -rf "${INSTALL_DIR}/api/tecnohead_solar_server" "${INSTALL_DIR}/migrations"
cp -R "${ROOT_DIR}/api/tecnohead_solar_server" "${INSTALL_DIR}/api/"
cp -R "${ROOT_DIR}/migrations" "${INSTALL_DIR}/"
"${INSTALL_DIR}/.venv/bin/python" -m pip install --upgrade pip >/dev/null
"${INSTALL_DIR}/.venv/bin/pip" install --disable-pip-version-check -r "${ROOT_DIR}/requirements.txt" >/dev/null

ENV_FILE="${INSTALL_DIR}/server.env"
umask 077
{
  printf 'SOLAR_DATABASE_URL=%s\n' "$(quote_env "${SOLAR_DATABASE_URL}")"
  printf 'SOLAR_API_TOKEN=%s\n' "$(quote_env "${SOLAR_API_TOKEN}")"
  printf 'SOLAR_DB_SCHEMA=%s\n' "$(quote_env "${SOLAR_DB_SCHEMA:-solar}")"
  printf 'SOLAR_RETENTION_DAYS=%s\n' "$(quote_env "${SOLAR_RETENTION_DAYS:-7}")"
  printf 'SOLAR_BIND_HOST=%s\n' "$(quote_env "${BIND_HOST}")"
  printf 'SOLAR_PORT=%s\n' "$(quote_env "${PORT}")"
} > "${ENV_FILE}"
chmod 0600 "${ENV_FILE}"

UNIT_FILE="${CONFIG_DIR}/${SERVICE_NAME}.service"
{
  printf '[Unit]\nDescription=TecnoHead Solar per-client API\nAfter=network-online.target\nWants=network-online.target\n\n[Service]\n'
  printf 'WorkingDirectory=%s\n' "${INSTALL_DIR}"
  printf 'EnvironmentFile=%s\n' "${ENV_FILE}"
  printf 'Environment=PYTHONPATH=%s/api\n' "${INSTALL_DIR}"
  printf 'ExecStart=%s tecnohead_solar_server.main:app --host %s --port %s\n' "${INSTALL_DIR}/.venv/bin/uvicorn" "${BIND_HOST}" "${PORT}"
  printf 'Restart=on-failure\nRestartSec=5\nNoNewPrivileges=true\nPrivateTmp=true\n\n[Install]\nWantedBy=default.target\n'
} > "${UNIT_FILE}"

if ! systemctl --user daemon-reload; then
  printf '%s\n' "systemd --user não está disponível; os arquivos foram instalados, mas o serviço não foi iniciado." >&2
  exit 2
fi
systemctl --user enable --now "${SERVICE_NAME}.service"

if command -v curl >/dev/null 2>&1; then
  for _ in {1..20}; do
    if curl --silent --fail --max-time 2 "http://127.0.0.1:${PORT}/api/v1/solar/health" \
      -H "Authorization: Bearer ${SOLAR_API_TOKEN}" >/dev/null; then
      printf 'TecnoHead Solar API ativa em %s:%s; schema=%s\n' "${BIND_HOST}" "${PORT}" "${SOLAR_DB_SCHEMA:-solar}"
      exit 0
    fi
    sleep 1
  done
fi

systemctl --user --no-pager --full status "${SERVICE_NAME}.service" || true
printf '%s\n' "O serviço foi iniciado, mas o health check não respondeu dentro do prazo." >&2
exit 3

