#!/usr/bin/env python3
"""Generate private and shareable human-readable QA reports."""

from __future__ import annotations

import argparse
import html
import os
import platform
import re
import subprocess
from datetime import datetime
from pathlib import Path


def latest_int(pattern: str, text: str, default: int = 0) -> int:
    matches = re.findall(pattern, text, re.MULTILINE)
    return int(matches[-1]) if matches else default


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--share-dir", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--status", choices=("APROBADO", "FALLIDO"), required=True)
    parser.add_argument("--phases", required=True)
    args = parser.parse_args()

    sha_result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    sha = sha_result.stdout.strip() if sha_result.returncode == 0 else "no disponible"
    log = args.log.read_text(encoding="utf-8", errors="replace") if args.log.exists() else ""
    django_runs = re.findall(r"Ran (\d+) tests? in[^\n]*(?:\(([^)]*)\))?", log)
    django_count = int(django_runs[-1][0]) if django_runs else 0
    django_skipped = int(re.search(r"skipped=(\d+)", django_runs[-1][1] or "").group(1)) if django_runs and re.search(r"skipped=(\d+)", django_runs[-1][1] or "") else 0
    django_failures = re.findall(r"FAILED \(([^)]*)\)", log)
    django_failed = sum(int(value) for value in re.findall(r"(?:failures|errors)=(\d+)", django_failures[-1])) if django_failures else 0
    front_count = latest_int(r"# tests (\d+)", log)
    front_pass = latest_int(r"# pass (\d+)", log)
    front_failed = latest_int(r"# fail (\d+)", log)
    front_skipped = latest_int(r"# skipped (\d+)", log)
    date = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    phase_rows = [phase.strip() for phase in args.phases.split(",") if phase.strip()]
    requirement_rows = re.findall(r"^\[REQ\] (.+)$", log, re.MULTILINE)
    error_rows = re.findall(r"^\[([^]]+)\] FALLIDO — (.+)$", log, re.MULTILINE)
    missing_rows = re.findall(r"^\[REQ\] FALTA: (.+)$", log, re.MULTILINE)
    smoke_rows = re.findall(r"^QA smoke passed: (.+)$", log, re.MULTILINE)
    phases_md = "\n".join(f"- {phase}" for phase in phase_rows) or "- No se completaron fases."
    phases_html = "".join(f"<tr><td>{html.escape(row)}</td></tr>" for row in phase_rows)
    requirements_md = "\n".join(f"- {row}" for row in requirement_rows) or "- No se pudo completar la comprobación de requisitos."
    requirements_html = "".join(f"<tr><td>{html.escape(row)}</td></tr>" for row in requirement_rows)
    error_md = "\n".join(f"- **{phase}:** {message}" for phase, message in error_rows) or "- No se registró un mensaje de error de fase. Revisa el siguiente paso indicado en pantalla."
    error_html = "".join(f"<li><b>{html.escape(phase)}:</b> {html.escape(message)}</li>" for phase, message in error_rows) or "<li>No se registró un mensaje de error de fase. Revisa el siguiente paso indicado en pantalla.</li>"
    missing_md = "\n".join(f"- {row}" for row in missing_rows) or "- No faltaron requisitos detectados."
    missing_html = "".join(f"<li>{html.escape(row)}</li>" for row in missing_rows) or "<li>No faltaron requisitos detectados.</li>"
    smoke_text = smoke_rows[-1] if smoke_rows else "El smoke funcional local no terminó o no se ejecutó. Consulta la fase y el log privado."
    overall_next = (
        "Revisa el informe y guarda la corrida junto a las evidencias manuales que agregues."
        if args.status == "APROBADO"
        else "Abre el informe, sigue el mensaje de solución y, si necesitas ayuda, comparte el informe y el log privado qa-run.log."
    )
    private_log = ".qa-private/runs (carpeta privada local; no se publica)"
    operating_system = f"{platform.system()} {platform.release()}"

    report = f"""# Resultado de validación QA

- Fecha y hora: {date}
- SHA validado: `{sha}`
- Estado general: **{args.status}**
- Sistema operativo: {operating_system} (la compatibilidad Windows 11 requiere validación manual en un equipo Windows real)
- Logs técnicos: `{private_log}`

## Requisitos detectados

{requirements_md}

## Pruebas automatizadas ejecutadas

| Grupo | Ejecutadas | Aprobadas | Fallidas | Omitidas |
|---|---:|---:|---:|---:|
| Django | {django_count} | {max(0, django_count - django_failed - django_skipped)} | {django_failed} | {django_skipped} |
| Frontend | {front_count} | {front_pass} | {front_failed} | {front_skipped} |

El conteo de Django refleja el último resumen de la suite que alcanzó a escribirse en el log. Si una fase falla antes de ejecutar pruebas, aparecerá como 0 y la fase indicará el motivo.

## Fases

{phases_md}

## Errores explicados

{error_md}

## Requisitos faltantes

{missing_md}

## Smoke funcional local

{smoke_text}

## Pruebas manuales o externas no ejecutadas por este asistente

No se consideran aprobadas Webpay E2E real completo, R2 externo con enlaces firmados y expiración real, SMTP real, pruebas de usabilidad externas ni rendimiento/carga en producción. Las pruebas automatizadas con dobles no comprueban esos servicios.

## Siguiente acción

{overall_next}

Si el resultado fue FALLIDO, comparte el informe en el PR. Comparte `qa-run.log` solo con soporte por un canal privado, nunca en GitHub. No compartas `.env.qa`, `.qa-private` completa, cookies, credenciales ni URLs firmadas.
"""
    status_class = "ok" if args.status == "APROBADO" else "fail"
    html_doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Informe QA BeatsCloud</title><style>
body{{font:16px/1.55 system-ui,sans-serif;max-width:850px;margin:2rem auto;padding:0 1rem;background:#10131d;color:#eee}}
h1,h2{{color:#ffd166}}.status{{padding:.8rem 1rem;border-radius:.6rem;font-weight:800;background:{'#153d2a' if status_class == 'ok' else '#4a1e28'};color:{'#84f1b3' if status_class == 'ok' else '#ff9aa9'}}}
code{{overflow-wrap:anywhere}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #394052;padding:.5rem;text-align:left}}.note{{color:#c6cad3}}
</style></head><body><h1>BEATSCLOUD — Informe de validación QA</h1>
<p class="status">RESULTADO: {html.escape(args.status)}</p>
<p><b>Fecha:</b> {html.escape(date)}<br><b>SHA:</b> <code>{html.escape(sha)}</code><br><b>Sistema operativo:</b> {html.escape(operating_system)}<br><b>Logs:</b> carpeta local privada <code>.qa-private/runs</code></p>
<h2>Requisitos detectados</h2><table>{requirements_html}</table>
<h2>Pruebas automatizadas</h2><table><thead><tr><th>Grupo</th><th>Ejecutadas</th><th>Aprobadas</th><th>Fallidas</th><th>Omitidas</th></tr></thead><tbody>
<tr><td>Django</td><td>{django_count}</td><td>{max(0, django_count - django_failed - django_skipped)}</td><td>{django_failed}</td><td>{django_skipped}</td></tr>
<tr><td>Frontend</td><td>{front_count}</td><td>{front_pass}</td><td>{front_failed}</td><td>{front_skipped}</td></tr></tbody></table>
<h2>Fases</h2><table>{phases_html}</table>
<h2>Errores explicados</h2><ul>{error_html}</ul>
<h2>Requisitos faltantes</h2><ul>{missing_html}</ul><h2>Smoke funcional local</h2><p>{html.escape(smoke_text)}</p>
<h2>No demostrado en esta ejecución</h2><p class="note">Webpay E2E real completo, R2 externo y expiración real de enlaces, SMTP real, usabilidad externa y rendimiento/carga productivos. Los mocks no validan esos servicios.</p>
<h2>Siguiente paso</h2><p>{html.escape(overall_next)}</p>
<p class="note">Si falla, enlaza el informe en el PR. Comparte qa-run.log solo por un canal privado con soporte, nunca en GitHub. No compartas .env.qa, contraseñas, tokens, cookies ni URLs firmadas.</p></body></html>
"""
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.share_dir.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    args.html.write_text(html_doc, encoding="utf-8")
    (args.share_dir / "INFORME_VALIDACION.md").write_text(report, encoding="utf-8")
    (args.share_dir / "INFORME_VALIDACION.html").write_text(html_doc, encoding="utf-8")
    os.chmod(args.out, 0o600)
    os.chmod(args.html, 0o600)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
