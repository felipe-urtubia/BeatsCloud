#!/usr/bin/env bash
set -euo pipefail

QA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
QA_ENV_FILE="$QA_ROOT/.env.qa"

qa_error() {
  printf 'QA setup error: %s\n' "$*" >&2
  exit 1
}

qa_load_env() {
  [[ -f "$QA_ENV_FILE" ]] || qa_error "No existe .env.qa. Ejecuta scripts/qa/setup.sh."
  [[ ! -L "$QA_ENV_FILE" ]] || qa_error ".env.qa no puede ser un enlace simbólico."
  local env_mode
  env_mode="$(stat -c '%a' "$QA_ENV_FILE")"
  [[ "$env_mode" == "600" ]] || qa_error ".env.qa debe tener permisos 0600 (actual: $env_mode)."
  set -a
  # shellcheck disable=SC1090
  source "$QA_ENV_FILE"
  set +a

  [[ "${DB_NAME:-}" == "beatscloud_qa_local" ]] || qa_error "DB_NAME no es la base QA aislada esperada."
  [[ "${DB_HOST:-}" == "127.0.0.1" ]] || qa_error "DB_HOST debe ser 127.0.0.1."
  [[ "${DB_PORT:-}" =~ ^[0-9]+$ ]] || qa_error "DB_PORT debe ser un puerto local del rango QA."
  local db_port=$((10#$DB_PORT))
  (( db_port >= 55433 && db_port <= 55499 )) || qa_error "DB_PORT debe estar entre 55433 y 55499."
  [[ "${QA_BACKEND_PORT:-}" == "8010" ]] || qa_error "QA_BACKEND_PORT debe ser 8010."
  [[ "${QA_FRONTEND_PORT:-}" == "3010" ]] || qa_error "QA_FRONTEND_PORT debe ser 3010."
  [[ "${DB_ENGINE:-}" == "django.db.backends.postgresql" ]] || qa_error "Solo se admite PostgreSQL local."
  [[ "${QA_PROJECT_NAME:-}" =~ ^beatscloud-qa-[a-f0-9]{8}$ ]] || qa_error "QA_PROJECT_NAME no tiene el formato generado."
  [[ "${R2_UPLOADS_ENABLED:-}" == "false" ]] || qa_error "R2 debe permanecer desactivado en QA local."
  [[ "${TRANSBANK_INTEGRATION_TYPE:-}" == "TEST" ]] || qa_error "QA local solo admite Webpay TEST."
  [[ "${EMAIL_BACKEND:-}" == "django.core.mail.backends.console.EmailBackend" ]] || qa_error "QA debe usar email de consola."
  [[ "${FRONTEND_URL:-}" == "http://127.0.0.1:3010" ]] || qa_error "FRONTEND_URL debe apuntar al frontend QA local."

  local external_var
  for external_var in \
    R2_ACCOUNT_ID R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_BUCKET_NAME \
    TRANSBANK_COMMERCE_CODE TRANSBANK_API_KEY EMAIL_HOST_USER EMAIL_HOST_PASSWORD \
    RESEND_API_KEY GMAIL_OAUTH_TOKEN_JSON; do
    [[ -z "${!external_var:-}" ]] || qa_error "$external_var debe estar vacío en .env.qa."
  done

  local expected_media actual_media
  expected_media="$QA_ROOT/media/qa"
  actual_media="$(realpath -m "${MEDIA_ROOT:-}")"
  [[ "$actual_media" == "$expected_media" ]] || qa_error "MEDIA_ROOT debe ser exactamente $expected_media."
  QA_RUNTIME_DIR="${TMPDIR:-/tmp}/${QA_PROJECT_NAME}-runtime"
  mkdir -p "$QA_RUNTIME_DIR"
  chmod 700 "$QA_RUNTIME_DIR"
}

qa_select_compose() {
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    QA_COMPOSE=(docker compose)
  elif command -v podman >/dev/null 2>&1 && podman info >/dev/null 2>&1; then
    QA_COMPOSE=(podman compose)
  else
    qa_error "Necesitas Docker Compose v2 o Podman con compose y acceso rootless."
  fi
}

qa_compose() {
  "${QA_COMPOSE[@]}" \
    --env-file "$QA_ENV_FILE" \
    --project-name "$QA_PROJECT_NAME" \
    --file "$QA_ROOT/compose.qa.yml" \
    "$@"
}

qa_assert_media_sentinel() {
  local expected="$QA_ROOT/media/qa"
  local actual="$(realpath -m "${MEDIA_ROOT:-}")"
  [[ "$actual" == "$expected" ]] || qa_error "Refusing to operate on media outside media/qa."
  [[ -f "$expected/.beatscloud-qa-media" ]] || qa_error "QA media sentinel is missing; refusing media cleanup."
}

qa_pid_matches() {
  local pid_file="$1" pattern="$2" pid cwd args
  [[ -f "$pid_file" ]] || return 1
  pid="$(cat "$pid_file")"
  [[ "$pid" =~ ^[0-9]+$ ]] || qa_error "Invalid PID file: $pid_file"
  kill -0 "$pid" 2>/dev/null || return 1
  cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
  args="$(ps -p "$pid" -o args= 2>/dev/null || true)"
  [[ "$args" == *"$pattern"* ]] && [[ "$cwd" == "$QA_ROOT" || "$cwd" == "$QA_ROOT/frontend/client" ]] \
    || qa_error "PID $pid is active but does not match this BeatsCloud QA process."
  return 0
}

qa_assert_stopped() {
  local file pattern
  for file in "$QA_RUNTIME_DIR/django.pid" "$QA_RUNTIME_DIR/vite.pid"; do
    if [[ "$file" == *django* ]]; then pattern="manage.py runserver"; else pattern="vite"; fi
    if qa_pid_matches "$file" "$pattern"; then
      qa_error "QA process is running; stop it with scripts/qa/stop.sh before reset."
    else
      rm -f "$file"
    fi
  done
}

qa_port_free() {
  python3 - "$1" <<'PY'
import socket, sys
sock = socket.socket()
try:
    sock.bind(("127.0.0.1", int(sys.argv[1])))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
PY
}

qa_find_db_port() {
  local port
  for port in $(seq 55433 55499); do
    if qa_port_free "$port"; then
      printf '%s\n' "$port"
      return 0
    fi
  done
  qa_error "No hay puertos libres en el rango QA 55433-55499."
}
