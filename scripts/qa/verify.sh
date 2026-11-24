#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
run_smoke=1
if [[ "${1:-}" == "--no-smoke" ]]; then
  run_smoke=0
elif [[ $# -gt 0 ]]; then
  qa_error "Opción no reconocida: $1"
fi
qa_load_env
qa_select_compose
qa_assert_media_sentinel

qa_compose exec -T db pg_isready -U "$DB_USER" -d "$DB_NAME"
qa_python "$QA_ROOT/manage.py" check
qa_python "$QA_ROOT/manage.py" makemigrations --check --dry-run
qa_python "$QA_ROOT/manage.py" test
(
  cd "$QA_ROOT/frontend/client"
  npm test
  npm run lint
  npm run build
)

if (( run_smoke )); then
  qa_python "$QA_ROOT/scripts/qa/smoke.py"
fi
