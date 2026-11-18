#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
qa_load_env
qa_select_compose
qa_assert_media_sentinel
qa_assert_stopped

echo "This resets only database beatscloud_qa_local and $MEDIA_ROOT."
echo "The Compose volume is retained; the local QA database contents will be erased."
read -r -p "Type RESET-QA to continue: " confirmation
[[ "$confirmation" == "RESET-QA" ]] || qa_error "Reset cancelled."

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

"$QA_ROOT/.venv/bin/python" "$QA_ROOT/manage.py" flush --noinput
expected="$QA_ROOT/media/qa"
actual="$(realpath -m "$MEDIA_ROOT")"
[[ "$actual" == "$expected" && -f "$actual/.beatscloud-qa-media" ]] \
  || qa_error "Media safety recheck failed; refusing to delete media."
rm -rf -- "$actual"
mkdir -p "$actual"
touch "$actual/.beatscloud-qa-media"
chmod 600 "$actual/.beatscloud-qa-media"

"$QA_ROOT/.venv/bin/python" "$QA_ROOT/manage.py" migrate --noinput
"$QA_ROOT/.venv/bin/python" "$QA_ROOT/manage.py" prepare_demo_catalog
"$QA_ROOT/.venv/bin/python" "$QA_ROOT/manage.py" prepare_qa_users --rotate-passwords
"$QA_ROOT/.venv/bin/python" "$QA_ROOT/manage.py" generate_qa_catalog --count 120 --seed 20261118
echo "QA reset and reseed complete. New temporary QA passwords were printed once above."
