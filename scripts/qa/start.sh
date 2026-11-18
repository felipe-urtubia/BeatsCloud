#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
qa_load_env
qa_select_compose

[[ -x "$QA_ROOT/.venv/bin/python" ]] || qa_error "Run scripts/qa/setup.sh first."
[[ -x "$QA_ROOT/frontend/client/node_modules/.bin/vite" ]] || qa_error "Run scripts/qa/setup.sh first."
qa_assert_media_sentinel
qa_compose up -d db

ready=0
for _ in $(seq 1 60); do
  if qa_compose exec -T db pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
[[ "$ready" == 1 ]] || qa_error "QA PostgreSQL is not ready."

"$QA_ROOT/.venv/bin/python" "$QA_ROOT/manage.py" migrate --noinput
"$QA_ROOT/.venv/bin/python" "$QA_ROOT/manage.py" prepare_demo_catalog
"$QA_ROOT/.venv/bin/python" "$QA_ROOT/manage.py" prepare_qa_users
"$QA_ROOT/.venv/bin/python" "$QA_ROOT/manage.py" generate_qa_catalog --count 120 --seed 20261118

for port in "$QA_BACKEND_PORT" "$QA_FRONTEND_PORT"; do
  if ! qa_port_free "$port"; then
    qa_error "Port $port is occupied by an unidentified process; it was not stopped."
  fi
done

cd "$QA_ROOT"
nohup "$QA_ROOT/.venv/bin/python" "$QA_ROOT/manage.py" runserver "127.0.0.1:$QA_BACKEND_PORT" \
  > "$QA_RUNTIME_DIR/django.log" 2>&1 &
echo "$!" > "$QA_RUNTIME_DIR/django.pid"

cd "$QA_ROOT/frontend/client"
nohup env VITE_API_MODE=hybrid VITE_DJANGO_URL= VITE_DJANGO_PROXY_TARGET="http://127.0.0.1:$QA_BACKEND_PORT" \
  "$QA_ROOT/frontend/client/node_modules/.bin/vite" --host 127.0.0.1 --port "$QA_FRONTEND_PORT" \
  > "$QA_RUNTIME_DIR/vite.log" 2>&1 &
echo "$!" > "$QA_RUNTIME_DIR/vite.pid"

for url in "http://127.0.0.1:$QA_BACKEND_PORT/api/session/" "http://127.0.0.1:$QA_FRONTEND_PORT/"; do
  ready=0
  for _ in $(seq 1 30); do
    if curl --silent --fail "$url" >/dev/null; then ready=1; break; fi
    sleep 1
  done
  [[ "$ready" == 1 ]] || qa_error "Service failed its HTTP readiness check: $url"
done

echo "Django: http://127.0.0.1:$QA_BACKEND_PORT"
echo "Vite:   http://127.0.0.1:$QA_FRONTEND_PORT"
echo "Logs:   $QA_RUNTIME_DIR/"
