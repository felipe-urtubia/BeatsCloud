#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
umask 077
qa_load_env
qa_select_compose

python_path="$(qa_venv_python_path)"
[[ -x "$python_path" ]] || qa_error "Falta el entorno Python. Ejecuta scripts/qa/setup.sh."
[[ -f "$QA_ROOT/frontend/client/node_modules/vite/bin/vite.js" ]] || qa_error "Falta Vite. Ejecuta scripts/qa/setup.sh."
qa_assert_media_sentinel
qa_private_dir "$QA_RUNTIME_DIR"
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

qa_python "$QA_ROOT/manage.py" migrate --noinput
qa_python "$QA_ROOT/manage.py" prepare_demo_catalog
qa_python "$QA_ROOT/manage.py" prepare_qa_users
qa_python "$QA_ROOT/manage.py" generate_qa_catalog --count 120 --seed 20261118

for port in "$QA_BACKEND_PORT" "$QA_FRONTEND_PORT"; do
  if ! qa_port_free "$port"; then
    qa_error "Port $port is occupied by an unidentified process; it was not stopped."
  fi
done

cd "$QA_ROOT"
python_media_root="$MEDIA_ROOT"
if qa_is_windows; then python_media_root="$(cygpath -aw "$MEDIA_ROOT")"; fi
nohup env MEDIA_ROOT="$python_media_root" "$python_path" "$QA_ROOT/manage.py" runserver --noreload "127.0.0.1:$QA_BACKEND_PORT" \
  > >("$(qa_system_python)" "$QA_ROOT/scripts/qa/private-log.py" "$QA_RUNTIME_DIR/django.log" --quiet >/dev/null 2>&1) 2>&1 &
echo "$!" > "$QA_RUNTIME_DIR/django.pid"

cd "$QA_ROOT/frontend/client"
nohup env VITE_API_MODE=hybrid VITE_DJANGO_URL= VITE_DJANGO_PROXY_TARGET="http://127.0.0.1:$QA_BACKEND_PORT" \
  node "$QA_ROOT/frontend/client/node_modules/vite/bin/vite.js" --host 127.0.0.1 --port "$QA_FRONTEND_PORT" \
  > >("$(qa_system_python)" "$QA_ROOT/scripts/qa/private-log.py" "$QA_RUNTIME_DIR/vite.log" --quiet >/dev/null 2>&1) 2>&1 &
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
