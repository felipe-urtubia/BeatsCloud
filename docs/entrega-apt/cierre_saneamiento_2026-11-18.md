# Cierre de saneamiento y publicación — 18-11-2026

## Propósito y alcance

Registro técnico de consolidación de `main`, inspección de historia, pruebas y actualización de referencias GitHub. No acredita rotación de credenciales externas ni purga de clones, forks, cachés o referencias internas alojadas por GitHub.

## Estado verificado antes de publicar

Consulta GitHub API/CLI del 18-11-2026:

| Referencia | SHA | Estado y acción prevista |
|---|---|---|
| `main` | `ec00e2e1e1ca51cddee00fa7d53ee8a47d08bdda` | Rama predeterminada, sin protección de rama observada; requiere actualización controlada con lease. |
| `frontend-trabajo` | `7ad680a7e022ab004386b183d5a8b043760b2a63` | Tres commits únicos cotejados por patch-id con `main` saneada; cerrar PR #2 y retirar rama tras publicar. |
| `integration/react-frontend` | `7b0424ab35f90c3874ada6cc26eeb9460b3fb5f2` | Punta ya contenida en el historial remoto de `main`; retirar rama tras verificar `main`. |
| Tags | Ninguno listado | No hay tags que retirar. |

PR #1 (integración React/Django) y PR #3 (descargas R2 temporales) estaban MERGED. PR #2 estaba OPEN. Su diff comparado contra `main` remota eliminaba implementaciones R2/Webpay, debido a su base atrasada; no se fusionó el tip. Sus tres commits únicos tienen patch-id equivalente en la candidata local: `6df926e` ↔ `f0c54f9`, `2d66714` ↔ `6883459`, `7ad680a` ↔ `750e49e` (SHA local previo a la actualización final de documentación). No se observaron workflows de GitHub Actions ni protección activa para `main`; la cuenta consultada tenía permiso de escritura.

## Aportes verificados en la candidata

- Felipe: PR #3 y commits de R2, Webpay, metadatos y validaciones del 17-11; equivalencias saneadas en [trazabilidad técnica](trazabilidad_tecnica.md). Los módulos R2/Webpay y sus pruebas están en el árbol final.
- Ismael: PR #1 y los tres commits únicos de PR #2; estos últimos cotejados por patch-id. Los cambios de React, carga, audio y documentación permanecen integrados.
- Vicente: no se encontró autoría, review ni evidencia Jira enlazada a su identidad en las fuentes consultables. No se atribuye QA individual por la sola existencia de la guía preparada para ejecutarlo.

## Historia y hallazgos de seguridad

- `agregar.html`/`agregar.zip` fueron ZIP accidentales; el listado histórico indicó un único `.env`. No se extrajo el miembro ni se publicaron valores.
- La auditoría remota identificó las rutas en el historial público anterior. El espejo privado previo a cambios conservó ramas y refs `refs/pull/*` para recuperación.
- La historia local candidata se reescribió con `git-filter-repo` 2.47.0. Un callback restringido a `settings.py`, `beatcloud/settings.py` y `server/settings.py` reemplazó defaults no vacíos de `DB_PASSWORD` y `DJANGO_SECRET_KEY`, sin sustituir coincidencias numéricas en fixtures. Se confirmó que los marcadores están limitados a esos módulos en el historial local.
- El escaneo de referencias alcanzables de la candidata no encontró `agregar.html`, `agregar.zip`, `.env`, `.env.qa`, bases de datos ni defaults sensibles no-placeholder. `.env.example` y `frontend/client/.env.example` contienen plantillas sin credenciales privadas.
- Requieren rotación/revocación confirmada por sus custodios: `DJANGO_SECRET_KEY`, `EMAIL_HOST_PASSWORD`, `TRANSBANK_API_KEY`, `DB_PASSWORD`, `R2_ACCESS_KEY_ID` y `R2_SECRET_ACCESS_KEY` que pudieron aparecer en el `.env` histórico. La rotación no está acreditada.
- Tras retirar ramas, pedir a GitHub Support evaluar purga de refs internas/cachés de PR: `refs/pull/1/head`, `refs/pull/2/head`, `refs/pull/2/merge` y `refs/pull/3/head`, que antes apuntaban a commits de la historia antigua. La actualización de ramas no permite asegurar su borrado.

## Respaldo privado

Respaldo remoto previo a operaciones, fuera del repositorio y permisos `0600/0700`:

- `/tmp/beatscloud-private-backup-final-20261118/github-mirror-before-publication-20261118T221914Z/all-advertised-refs.bundle`
- SHA-256: `ab90825981e01f72fec7f065961120ff78bd70ef173177d6092ea81ad67053a2`
- `git bundle verify` aprobó; incluye las refs anunciadas antes de limpiar. Contiene historia sensible y es solo recuperación privada.

Respaldo de `main` local previa a la última sanitización:

- `/tmp/beatscloud-private-backup-final-20261118/local-main-before-final-sanitization-20261118T222214Z.bundle`
- SHA-256: `eb727dca5ceebc32b95eedd924ef6f2a44fced1ba3236e86b5b2b1a89b5c20c4`
- `git bundle verify` aprobó. Contiene defaults históricos y no debe compartirse.

El archivo de código fuente anterior `beatscloud-main-source-a0ee281.tar.gz` corresponde al corte anterior; no es la versión final de entrega. Se generará una nueva copia de código final sin `.git`, `.env`, base, media ni respaldos después de cerrar documentación.

## Pruebas del código candidato

La candidata `c91a7d0` pasó `scripts/qa/verify.sh` el 18-11-2026:

- Django: 372 tests OK (151.437 s).
- Frontend: 26/26 tests OK.
- `manage.py check`, `makemigrations --check --dry-run`, lint (`tsc -b`) y build aprobados.
- Build: Vite transformó 1.926 módulos.
- HTTP local: frontend/backend listos; catálogo con 125 pistas en 21 páginas.

No valida Firefox manual, Webpay real, R2 real, SMTP real ni despliegue. Los logs/tests Webpay y R2 usan dobles; los servicios externos no se probaron.

## Estado de publicación

Al crear este registro, la publicación aún estaba pendiente de actualizar `main` con lease, cerrar PR #2 y retirar ramas obsoletas. El resultado y los SHA finales se completarán en una actualización posterior de este documento una vez verificadas esas operaciones.
