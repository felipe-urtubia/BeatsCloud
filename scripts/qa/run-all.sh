#!/usr/bin/env bash
set -uo pipefail

QA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$QA_ROOT"
source "$QA_ROOT/scripts/qa/common.sh"
umask 077

stamp="$(date +%Y%m%d-%H%M%S)"
run_dir="$QA_ROOT/.qa-private/runs/$stamp"
mkdir -p "$run_dir"
chmod 700 "$QA_ROOT/.qa-private" "$QA_ROOT/.qa-private/runs" "$run_dir"
run_lock="$QA_ROOT/.qa-private/run.lock"
if ! mkdir "$run_lock" 2>/dev/null; then
  say_lock="Ya hay otra validación en curso o quedó un bloqueo sin cerrar. No abras otra ventana; reinicia el asistente cuando la ejecución anterior haya terminado."
  printf '%s\n' "$say_lock" >&2
  exit 1
fi
printf '%s\n' "$$" > "$run_lock/pid"
run_log="$run_dir/qa-run.log"
: > "$run_log"
chmod 600 "$run_log"
export QA_PRIVATE_LOG_DIR="$run_dir"
export QA_RUN_LOG="$run_log"

status="FALLIDO"
setup_status="PENDIENTE"
requirements_status="PENDIENTE"
start_status="PENDIENTE"
tests_status="PENDIENTE"
smoke_status="PENDIENTE"
stop_status="PENDIENTE"
report_status="PENDIENTE"
stop_attempted=0
finished=0

release_run_lock() { rm -f "$run_lock/pid"; rmdir "$run_lock" 2>/dev/null || true; }

say() { printf '%s\n' "$*"; }
log_command() {
  local label="$1"; shift
  say "$label"
  set +e
  "$@" 2>&1 | "$(qa_system_python)" "$QA_ROOT/scripts/qa/private-log.py" "$run_log" --summary
  local result=${PIPESTATUS[0]}
  set -e
  return "$result"
}
step_fail() {
  local phase="$1" reason="$2"
  say "La fase falló: $reason"
  printf '[%s] FALLIDO — %s\n' "$phase" "$reason" >> "$run_log"
  return 1
}
write_report() {
  local final_status="$1"
  local phases=""
  [[ "$requirements_status" == "OK" ]] && phases+="Requisitos: correctos, " || phases+="Requisitos: $requirements_status, "
  [[ "$setup_status" == "OK" ]] && phases+="Preparación: correcta, " || phases+="Preparación: $setup_status, "
  [[ "$start_status" == "OK" ]] && phases+="Inicio de servicios: correcto, " || phases+="Inicio de servicios: $start_status, "
  [[ "$tests_status" == "OK" ]] && phases+="Pruebas y checks: correctos, " || phases+="Pruebas y checks: $tests_status, "
  [[ "$smoke_status" == "OK" ]] && phases+="Smoke local: correcto, " || phases+="Smoke local: $smoke_status, "
  [[ "$stop_status" == "OK" ]] && phases+="Detención: correcta" || phases+="Detención: $stop_status"
  local report_python
  report_python="$(qa_system_python 2>/dev/null || true)"
  if [[ -n "$report_python" ]]; then
    "$report_python" "$QA_ROOT/scripts/qa/write-report.py" --out "$run_dir/INFORME_VALIDACION.md" --html "$run_dir/INFORME_VALIDACION.html" --share-dir "$QA_ROOT/evidencias/qa/runs/$stamp" --log "$run_log" --status "$final_status" --phases "$phases" >/dev/null 2>&1 || return 1
  else
    cat > "$run_dir/INFORME_VALIDACION.md" <<EOF
# Resultado de validación QA

- Fecha: $(date '+%Y-%m-%d %H:%M %Z')
- Commit probado: $(git rev-parse HEAD)
- Estado general: **$final_status**
- Logs técnicos privados: `.qa-private/runs/$stamp`

El informe completo no pudo consultar Python del sistema. Comparte qa-run.log si hubo un error.
EOF
    mkdir -p "$QA_ROOT/evidencias/qa/runs/$stamp"
    cp "$run_dir/INFORME_VALIDACION.md" "$QA_ROOT/evidencias/qa/runs/$stamp/INFORME_VALIDACION.md"
    cat > "$run_dir/INFORME_VALIDACION.html" <<EOF
<!doctype html><html lang="es"><meta charset="utf-8"><title>Informe QA BeatsCloud</title><h1>Resultado QA: $final_status</h1><p>Revisa el informe Markdown. No compartas credenciales ni .env.qa.</p></html>
EOF
    cp "$run_dir/INFORME_VALIDACION.html" "$QA_ROOT/evidencias/qa/runs/$stamp/INFORME_VALIDACION.html"
  fi
  chmod 600 "$run_dir/INFORME_VALIDACION.md" "$run_dir/INFORME_VALIDACION.html"
}
emergency_stop() {
  if (( stop_attempted == 0 )) && [[ -f "$QA_ENV_FILE" ]]; then
    stop_attempted=1
    say "Deteniendo de forma segura los servicios QA..."
    set +e
    "$QA_ROOT/scripts/qa/stop.sh" 2>&1 | "$(qa_system_python)" "$QA_ROOT/scripts/qa/private-log.py" "$run_log" --summary
    local result=${PIPESTATUS[0]}
    set -e
    if (( result == 0 )); then stop_status="OK"; else stop_status="FALLIDO (revisa el log)"; fi
  fi
}
on_exit() {
  local original=$?
  if (( finished == 0 )); then
    emergency_stop
    write_report "FALLIDO" || true
    say "Informe: $run_dir/INFORME_VALIDACION.md"
    say "Informe para compartir: evidencias/qa/runs/$stamp/INFORME_VALIDACION.html o .md"
    say "Log técnico privado: $run_log"
  fi
  release_run_lock
  exit "$original"
}
trap on_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

say "BEATSCLOUD — VALIDACIÓN QA"
say "Bienvenido. Esta ejecución prepara el entorno, valida el proyecto y conserva sus datos QA."
say "Los archivos técnicos quedan en .qa-private; no compartas .env.qa."

say "[1/7] Revisando requisitos..."
missing=()
command -v git >/dev/null 2>&1 || missing+=("Git: necesario para descargar y comprobar el proyecto. Instala Git desde https://git-scm.com/downloads y vuelve a ejecutar el asistente.")
command -v bash >/dev/null 2>&1 || missing+=("Bash: necesario para ejecutar el asistente. Instala Git for Windows (Windows) o Bash desde tu distribución Linux y vuelve a ejecutar el asistente.")
if qa_is_windows; then
  windows_build="$(powershell.exe -NoProfile -Command '[Environment]::OSVersion.Version.Build' 2>/dev/null | tr -d '\r' || true)"
  [[ "$windows_build" =~ ^[0-9]+$ ]] && printf '[REQ] Windows 11 build %s: detectado.\n' "$windows_build" >> "$run_log" || true
  [[ "$windows_build" =~ ^[0-9]+$ ]] && (( windows_build >= 22000 )) || missing+=("Windows 11: esta entrada requiere Windows 11 (compilación 22000 o posterior). Consulta Configuración > Sistema > Acerca de y usa un equipo Windows 11.")
  command -v cygpath >/dev/null 2>&1 || missing+=("Git Bash completo: falta cygpath. Reinstala Git for Windows y vuelve a abrir el asistente.")
  command -v icacls.exe >/dev/null 2>&1 || missing+=("Permisos privados de Windows: no encuentro icacls.exe. Repara la instalación de Windows y vuelve a ejecutar el asistente.")
  command -v curl >/dev/null 2>&1 || missing+=("curl: se necesita para comprobar que los servicios QA respondan. Instala Git for Windows actualizado y vuelve a abrir el asistente.")
else
  command -v curl >/dev/null 2>&1 || missing+=("curl: se necesita para comprobar los servicios. Instala curl con el gestor de tu distribución y vuelve a ejecutar el asistente.")
fi
python_cmd="$(qa_system_python 2>/dev/null || true)"
if [[ -z "$python_cmd" ]]; then
  missing+=("Python 3.12 o superior: necesario para preparar el entorno. Instálalo desde https://www.python.org/downloads/ y marca la opción para añadirlo al PATH; luego vuelve a ejecutar el asistente.")
else
  "$python_cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)' 2>/dev/null || missing+=("Python 3.12 o superior: la versión encontrada es antigua. Actualiza Python y vuelve a ejecutar el asistente.")
fi
if ! node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 20 ? 0 : 1)' >/dev/null 2>&1; then
  missing+=("Node.js 20 o superior: necesario para instalar y compilar el frontend. Instala la versión LTS desde https://nodejs.org/ y vuelve a ejecutar el asistente.")
fi
npm --version >/dev/null 2>&1 || missing+=("npm: se instala junto con Node.js. Reinstala Node.js LTS y vuelve a ejecutar el asistente.")
if qa_is_windows; then
  command -v docker >/dev/null 2>&1 || missing+=("Docker Desktop: se necesita para crear la base PostgreSQL aislada. Instala Docker Desktop desde https://www.docker.com/products/docker-desktop/ y vuelve a ejecutar el asistente.")
  if command -v docker >/dev/null 2>&1; then
    docker compose version >/dev/null 2>&1 || missing+=("Docker Compose v2: viene con Docker Desktop actual. Actualiza Docker Desktop y vuelve a ejecutar el asistente.")
    docker info >/dev/null 2>&1 || missing+=("Docker Desktop no está iniciado. Ábrelo, espera a que indique que está listo y vuelve a ejecutar INICIAR_QA.bat.")
  fi
elif command -v docker >/dev/null 2>&1; then
  docker compose version >/dev/null 2>&1 || missing+=("Docker Compose v2: necesario para la base PostgreSQL QA. Instala Docker Desktop (Windows) o Docker Engine con Compose (Linux), inicia Docker y vuelve a ejecutar el asistente.")
  docker info >/dev/null 2>&1 || missing+=("Docker no está iniciado o no tienes acceso. Inicia Docker Desktop / el servicio Docker y vuelve a ejecutar el asistente.")
elif command -v podman >/dev/null 2>&1; then
  podman compose version >/dev/null 2>&1 || missing+=("Podman Compose: necesario para la base PostgreSQL QA. Instala Podman y el complemento Compose según tu distribución; vuelve a ejecutar el asistente.")
  podman info >/dev/null 2>&1 || missing+=("Podman no está listo. Inicia el entorno rootless de Podman y vuelve a ejecutar el asistente.")
else
  missing+=("Docker Compose v2 o Podman Compose: necesario para la base PostgreSQL. Instala Docker Desktop (Windows) o Docker/Podman en Linux y vuelve a ejecutar el asistente.")
fi
command -v ffmpeg >/dev/null 2>&1 || missing+=("FFmpeg: necesario para preparar previews de audio. Instálalo desde https://ffmpeg.org/download.html (o con el gestor de paquetes de Linux) y vuelve a ejecutar el asistente.")
if ! git diff --quiet HEAD; then
  missing+=("El código del clon tiene cambios sin guardar en un commit. Para poder identificar exactamente lo que se probó, usa un clon limpio de main y vuelve a ejecutar INICIAR_QA.")
fi
for req in Git Bash Python Node.js npm Docker Docker-Compose FFmpeg; do
  case "$req" in
    Git) command -v git >/dev/null 2>&1 && result=detectado || result=falta ;;
    Bash) command -v bash >/dev/null 2>&1 && result=detectado || result=falta ;;
    Python) [[ -n "$python_cmd" ]] && result=detectado || result=falta ;;
    Node.js) command -v node >/dev/null 2>&1 && result=detectado || result=falta ;;
    npm) command -v npm >/dev/null 2>&1 && result=detectado || result=falta ;;
    Docker) command -v docker >/dev/null 2>&1 && result=detectado || result=falta ;;
    Docker-Compose) if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then result=detectado; else result=falta; fi ;;
    FFmpeg) command -v ffmpeg >/dev/null 2>&1 && result=detectado || result=falta ;;
  esac
  printf '[REQ] %s: %s.\n' "$req" "$result" >> "$run_log"
done
if git diff --quiet HEAD; then
  printf '[REQ] Código rastreado del clon: limpio.\n' >> "$run_log"
else
  printf '[REQ] Código rastreado del clon: modificado.\n' >> "$run_log"
fi
if [[ -n "$python_cmd" ]]; then printf '[REQ] Python version: %s.\n' "$("$python_cmd" --version 2>&1)" >> "$run_log"; fi
command -v node >/dev/null 2>&1 && printf '[REQ] Node.js version: %s.\n' "$(node --version 2>/dev/null)" >> "$run_log" || true
command -v npm >/dev/null 2>&1 && printf '[REQ] npm version: %s.\n' "$(npm --version 2>/dev/null)" >> "$run_log" || true
command -v ffmpeg >/dev/null 2>&1 && printf '[REQ] FFmpeg: %s.\n' "$(ffmpeg -version 2>/dev/null | head -n 1)" >> "$run_log" || true
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  printf '[REQ] Docker Desktop / daemon: iniciado.\n' >> "$run_log"
else
  printf '[REQ] Docker Desktop / daemon: no iniciado o no disponible.\n' >> "$run_log"
fi
if [[ -n "$python_cmd" ]]; then
  for port in 8010 3010; do
    "$python_cmd" - "$port" <<'PY' >/dev/null 2>&1 || missing+=("Puerto local $port: está ocupado. Cierra el programa que lo usa y vuelve a ejecutar el asistente.")
import socket, sys
s = socket.socket()
try:
    s.bind(("127.0.0.1", int(sys.argv[1])))
finally:
    s.close()
PY
  done
fi
if (( ${#missing[@]} )); then
  requirements_status="FALLIDO"
  for item in "${missing[@]}"; do say "- $item"; printf '[REQ] FALTA: %s\n' "$item" >> "$run_log"; done
  step_fail "requisitos" "Faltan componentes necesarios. Instálalos y vuelve a abrir INICIAR_QA." || true
  write_report "FALLIDO" || true
  finished=1
  say "RESULTADO: FALLIDO"
  say "Informe: $run_dir/INFORME_VALIDACION.md"
  say "Informe para compartir: evidencias/qa/runs/$stamp/INFORME_VALIDACION.html o .md"
  say "Comparte el informe por Pull Request; entrega qa-run.log solo a soporte por un canal privado. Nunca subas .qa-private a GitHub."
  exit 1
fi
requirements_status="OK"
say "Requisitos básicos encontrados."

say "[2/7] Preparando entorno QA..."
if log_command "Instalando dependencias y preparando datos locales..." "$QA_ROOT/scripts/qa/setup.sh"; then setup_status="OK"; else setup_status="FALLIDO"; step_fail "preparación" "No se pudo preparar el entorno." || true; exit 1; fi

say "[3/7] Iniciando servicios..."
if log_command "Iniciando base de datos, backend y frontend..." "$QA_ROOT/scripts/qa/start.sh"; then start_status="OK"; else start_status="FALLIDO"; step_fail "inicio" "No se pudieron iniciar los servicios." || true; exit 1; fi

say "[4/7] Ejecutando pruebas..."
if log_command "Ejecutando checks, migraciones, pruebas Django, frontend, TypeScript, lint y build..." "$QA_ROOT/scripts/qa/verify.sh" --no-smoke; then tests_status="OK"; else tests_status="FALLIDO"; step_fail "pruebas" "Falló una prueba o un check." || true; exit 1; fi

say "[5/7] Ejecutando pruebas de funcionamiento..."
if log_command "Comprobando Vite, proxy, catálogo, preview y permisos de descarga..." bash -c 'source "$1/scripts/qa/common.sh"; qa_load_env; qa_python "$1/scripts/qa/smoke.py"' _ "$QA_ROOT"; then smoke_status="OK"; else smoke_status="FALLIDO"; step_fail "smoke" "Falló una comprobación de funcionamiento local." || true; exit 1; fi

say "[6/7] Deteniendo servicios..."
stop_attempted=1
if log_command "Deteniendo procesos QA y PostgreSQL, conservando la base y los archivos QA..." "$QA_ROOT/scripts/qa/stop.sh"; then stop_status="OK"; else stop_status="FALLIDO"; step_fail "detención" "No se confirmó que todos los servicios se detuvieran." || true; exit 1; fi

say "[7/7] Generando informe final..."
if write_report "APROBADO"; then report_status="OK"; status="APROBADO"; else report_status="FALLIDO"; status="FALLIDO"; fi
finished=1
if [[ "$report_status" == "OK" ]]; then
  say "RESULTADO: APROBADO"
  say "Las fases de validación y detención finalizaron correctamente."
else
  say "RESULTADO: FALLIDO — no se pudo escribir el informe automático."
fi
say "Informe: $run_dir/INFORME_VALIDACION.md"
say "Informe para compartir: evidencias/qa/runs/$stamp/INFORME_VALIDACION.html o .md"
say "Log técnico privado: $run_log"
say "Conserva esos archivos; el informe indica cuál enviar si necesitas ayuda."
[[ "$status" == "APROBADO" ]]
