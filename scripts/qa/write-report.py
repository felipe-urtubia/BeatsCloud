#!/usr/bin/env python3
"""Write a plain-language final QA report from the run's private log."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--status", choices=("APROBADO", "FALLIDO"), required=True)
    parser.add_argument("--phases", required=True)
    args = parser.parse_args()
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    content = args.log.read_text(encoding="utf-8", errors="replace") if args.log.exists() else ""
    django = re.findall(r"Ran (\d+) tests? in", content)
    django_failure_blocks = re.findall(r"FAILED \(([^)]*)\)", content)
    frontend_tests = re.findall(r"# tests (\d+)", content)
    frontend_pass = re.findall(r"# pass (\d+)", content)
    frontend_fail = re.findall(r"# fail (\d+)", content)
    django_count = int(django[-1]) if django else 0
    django_failed = 0
    if django_failure_blocks:
        django_failed = sum(int(value) for value in re.findall(r"(?:failures|errors)=(\d+)", django_failure_blocks[-1]))
    front_count = int(frontend_tests[-1]) if frontend_tests else 0
    front_pass_count = int(frontend_pass[-1]) if frontend_pass else 0
    front_fail_count = int(frontend_fail[-1]) if frontend_fail else 0
    phases = [phase.strip() for phase in args.phases.split(",") if phase.strip()]
    rows = "\n".join(f"- {phase}" for phase in phases)
    try:
        log_location = args.log.parent.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        log_location = Path(".qa-private/runs")
    date = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    next_step = (
        "La validación terminó. Conserva este informe y el directorio de logs."
        if args.status == "APROBADO"
        else "Envía este informe y el archivo qa-run.log del directorio privado indicado. No borres ese directorio."
    )
    report = f"""# Resultado de validación QA

- Fecha: {date}
- Commit probado: `{sha or 'no disponible'}`
- Estado general: **{args.status}**
- Pruebas Django ejecutadas: {django_count} (aprobadas: {max(0, django_count - django_failed) if django else 0}, fallidas: {django_failed})
- Pruebas frontend ejecutadas: {front_count} (aprobadas: {front_pass_count}, fallidas: {front_fail_count})
- Logs técnicos privados: `{log_location}`

## Fases

{rows or '- No se completaron fases.'}

## Qué comprueba esta ejecución

Checks de Django, migraciones, pruebas automatizadas del backend y frontend, TypeScript, lint, build y smoke local de Vite, proxy, catálogo, preview y rechazo de descarga anónima.

## Límites de la evidencia

Esta ejecución no demuestra una compra Webpay E2E real completa, credenciales productivas de Webpay, funcionamiento real de R2 ni expiración de enlaces firmados contra el servicio externo, envío SMTP real, usabilidad con personas externas ni carga/concurrencia en infraestructura productiva. Las pruebas automatizadas locales no equivalen a esas verificaciones externas.

## Siguiente acción

{next_step}
"""
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    os.chmod(args.out, 0o600)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
