#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -t 0 ]]; then
  if command -v x-terminal-emulator >/dev/null 2>&1; then
    exec x-terminal-emulator -e bash -lc 'cd "$1" && exec ./INICIAR_QA.sh' qa "$ROOT"
  elif command -v gnome-terminal >/dev/null 2>&1; then
    exec gnome-terminal -- bash -lc 'cd "$1" && exec ./INICIAR_QA.sh' qa "$ROOT"
  elif command -v konsole >/dev/null 2>&1; then
    exec konsole -e bash -lc 'cd "$1" && exec ./INICIAR_QA.sh' qa "$ROOT"
  fi
  printf 'Abre esta carpeta en una terminal y ejecuta: ./INICIAR_QA.sh\n'
  exit 2
fi
"$ROOT/scripts/qa/run-all.sh"
result=$?
printf '\nLa validación terminó. Esta ventana quedará abierta. Presiona Enter para cerrarla... '
read -r _
exit "$result"
