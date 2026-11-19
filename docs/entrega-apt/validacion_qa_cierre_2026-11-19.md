# Validación automatizada de cierre — 19-11-2026

## Alcance y versión

Validación local repetida sobre el árbol de producto `7ad7305fecdbdeff8b4f9d8c301b1f6f1c3e7dbe`, posterior a los commits remotos `d4d6bf6` (elimina el valor predeterminado de contraseña de PostgreSQL) y `68acadd` (agrega rewrites Vercel). La suite completa de 372 pruebas Django, 26 frontend, TypeScript/lint, build y smoke terminó correctamente sobre ese árbol. Luego se probó `bash build.sh` con `.env.qa` cargado; collectstatic y migraciones también terminaron correctamente. Los cambios posteriores `cbebac5` y el commit que actualiza este reporte son documentales; la configuración Vercel no se probó en un despliegue externo.

Entorno: Linux, Python 3.14, Django 6.0.6, PostgreSQL 16 en Docker Compose local, Node 22 y npm 10. Se usó `.env.qa` local con modo `0600`, base `beatscloud_qa_local`, R2 desactivado, Webpay TEST sin credenciales, email de consola y medios bajo `media/qa`. No se conectaron servicios externos ni bases de datos de producto.

## Resultados

| Comprobación | Resultado | Alcance |
|---|---|---|
| `scripts/qa/setup.sh` | OK | PostgreSQL QA aislado, migraciones y datos sintéticos locales. El puerto predeterminado 55433 estaba ocupado por un contenedor QA de otro checkout; se usó 55434 sin detener ni reutilizar ese contenedor. |
| `manage.py check` | OK | Sin errores del sistema Django. |
| `makemigrations --check --dry-run` | OK | No se detectaron migraciones pendientes. |
| Suite Django | **372/372 OK** | Pruebas automatizadas con dobles para proveedores externos donde corresponde. No son una prueba manual ni una transacción real de Webpay. |
| Frontend Node | **26/26 OK** | Casos unitarios sobre checkout, navegación y estado de subida. |
| TypeScript/lint (`npm run lint`) | OK | `tsc -b` sin errores. |
| Build Vite | OK | 1.926 módulos transformados; build de producción local. |
| Smoke HTTP local | OK | Frontend en `127.0.0.1:3010`, sesión Django y catálogo; la primera página mostró 6 de 125 pistas, 21 páginas. |
| `bash -n scripts/qa/*.sh` | OK | Sintaxis de scripts QA. |
| `bash build.sh` con `.env.qa` y `.venv` | OK | `collectstatic` confirmó 141 estáticos; migraciones sin cambios. No se ejecutó un despliegue Render. |

La ejecución repetida tras incorporar los commits remotos inició PostgreSQL QA, no detectó migraciones nuevas, pasó `manage.py check`, ejecutó 372/372 pruebas Django y completó 26/26 frontend, TypeScript/lint, build y smoke HTTP. La llamada inicial de la preparación anterior a `verify.sh` ocurrió antes de iniciar los servicios y falló en el smoke HTTP; se inició el entorno y la ejecución posterior pasó. La repetición actual volvió a pasar desde el árbol rebased.

En la repetición del corte actualizado se cargó `.env.qa` y se ejecutaron `manage.py check`, `makemigrations --check --dry-run` y `bash build.sh`: collectstatic dejó 141 archivos sin cambios y no hubo migraciones por aplicar. El intento inicial de la preparación anterior sin `.env.qa` recibió conexión rechazada al PostgreSQL local 5432; no aplicó migraciones.

Durante `manage.py test`, WhiteNoise advirtió que `staticfiles/` aún no existía; `collectstatic` posterior creó los archivos esperados. No hubo fallo de pruebas asociado.

## Lo que esta validación no demuestra

No se ejecutó Firefox manual ni un recorrido E2E de navegador. No se completó compra y descarga de extremo a extremo; Webpay TEST real, Cloudflare R2 real, SMTP real y despliegue externo siguen sin evidencia de ejecución. Los resultados mockeados o automatizados no se presentan como operaciones reales.

Los casos preparados por Vicente mantienen su autoría de diseño. Esta ejecución fue automatizada por el runner local; no se atribuye a Vicente ni a una ejecución manual de Ismael. El documento E2E reportado por Vicente no se recuperó; véase el registro de evidencia correspondiente.

## Reproducibilidad y cuidado del entorno

Para repetir, crear/clonar el código, instalar dependencias y ejecutar `scripts/qa/setup.sh`, `scripts/qa/start.sh`, `scripts/qa/verify.sh`; al finalizar, usar `scripts/qa/stop.sh`. El setup selecciona un puerto libre solo dentro de 55433–55499 para una configuración nueva. `.env.qa`, sus claves temporales, datos sintéticos, volúmenes y medios son locales y no se versionan. No reutilizar contraseñas o datos de demostración fuera del entorno aislado.
