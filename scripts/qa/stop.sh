#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
umask 077
qa_load_env

stop_one() {
  local pid_file="$1" pattern="$2" pid
  if ! qa_pid_matches "$pid_file" "$pattern"; then
    rm -f "$pid_file"
    return
  fi
  pid="$(cat "$pid_file")"
  kill -TERM "$pid"
  for _ in $(seq 1 15); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 1
  done
  if kill -0 "$pid" 2>/dev/null; then
    qa_error "Process $pid did not stop cleanly; no forced kill was issued."
  fi
  rm -f "$pid_file"
}

stop_one "$QA_RUNTIME_DIR/vite.pid" vite
stop_one "$QA_RUNTIME_DIR/django.pid" 'manage.py runserver'
for port in "$QA_FRONTEND_PORT" "$QA_BACKEND_PORT"; do
  port_closed=0
  for _ in $(seq 1 15); do
    if qa_port_free "$port"; then port_closed=1; break; fi
    sleep 1
  done
  [[ "$port_closed" == 1 ]] || qa_error "El puerto QA $port sigue ocupado. No se detuvo ningún proceso ajeno; revisa quién lo está usando."
done
qa_select_compose
qa_compose stop db
echo "QA services stopped; the database volume and QA media were retained."
