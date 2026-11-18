#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
qa_load_env
qa_select_compose
qa_assert_media_sentinel

qa_compose exec -T db pg_isready -U "$DB_USER" -d "$DB_NAME"
"$QA_ROOT/.venv/bin/python" "$QA_ROOT/manage.py" check
"$QA_ROOT/.venv/bin/python" "$QA_ROOT/manage.py" makemigrations --check --dry-run
"$QA_ROOT/.venv/bin/python" "$QA_ROOT/manage.py" test
(
  cd "$QA_ROOT/frontend/client"
  npm test
  npm run lint
  npm run build
)

curl --fail --silent --show-error "http://127.0.0.1:$QA_FRONTEND_PORT/" >/dev/null
curl --fail --silent --show-error "http://127.0.0.1:$QA_BACKEND_PORT/api/session/" >/dev/null
curl --fail --silent --show-error "http://127.0.0.1:$QA_BACKEND_PORT/api/catalogo/" \
  | "$QA_ROOT/.venv/bin/python" -c 'import json,sys; d=json.load(sys.stdin); print("Catalog first page:", len(d["tracks"]), "of", d["total_resultados"], "tracks; pages:", d["total_paginas"])'
