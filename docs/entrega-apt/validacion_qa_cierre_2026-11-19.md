# Validación QA de cierre — 19-11-2026

## Referencias Git comprobadas

- **Commit de producto donde se repitió la suite Django, `manage.py check`, `makemigrations --check --dry-run`, `build.sh` y smoke HTTP:** `4569613b29e7023161149ca5e7d5fddabf6437db` (`4569613`). Contiene los commits remotos de correo Resend/Gmail y la protección QA de proveedores externos.
- **Último corte histórico de la suite frontend de 26 pruebas, TypeScript/lint y build Vite:** `7ad7305fecdbdeff8b4f9d8c301b1f6f1c3e7dbe`, según el registro de ejecución anterior. Entre ese corte y el de este documento no cambió el código fuente del frontend; el corte actual sí integra correo en backend y los guards QA.
- El commit `12a3ea0` documenta un corte anterior; `e48174f` fue un snapshot local de cierre previo. No son la versión vigente. `8468063` y `92c39dc` eran referencias cortas residuales de documentos anteriores, no se usan como versión actual.
- El snapshot académico definitivo debe señalar el commit final de documentación del producto y verificar sus hashes; el snapshot identifica el corte documental, no retroactivamente el commit de ejecución de pruebas.

## Ejecuciones actuales sobre `4569613b29e7023161149ca5e7d5fddabf6437db`

Entorno Linux, Python 3.14, Django 6.0.6, PostgreSQL 16 aislado en el contenedor del worktree de cierre, Node 22/npm 10. `.env.qa` local modo 0600; DB `beatscloud_qa_local`, host `127.0.0.1`, puerto QA dentro de 55433–55499; correo console, Gmail/Resend/SMTP sin credenciales, R2 desactivado y Webpay TEST sin secretos.

| Comprobación | Resultado | Interpretación |
|---|---:|---|
| Guardas `.env.qa` y configuración QA | OK | Verifican host, puerto QA, medios, permisos 0600, correo console y credenciales externas vacías; no permiten symlink. |
| `manage.py check` | OK | Django inicializa con AnyMail/Gmail API instalados; no se envió correo. |
| `makemigrations --check --dry-run` | OK | No hay migraciones pendientes. |
| Suite Django | **372/372 OK** | Runner automatizado en `4569613b29e7023161149ca5e7d5fddabf6437db`; proveedores externos no contactados. |
| `bash build.sh` | OK | Dependencias instaladas, `collectstatic`: 141 sin cambios, migraciones: ninguna. Ejecución local; no prueba Render. |
| Smoke HTTP local | OK | Django/Vite locales; sesión responde; catálogo 6 de 125 pistas, 21 páginas. Servicios QA iniciados y luego detenidos con script del worktree; volumen/medios retenidos. |
| Frontend: 26 tests, `tsc -b`, lint y build Vite | **OK en corte histórico** | Se conserva la ejecución registrada en `7ad7305…`; no se repitió porque la aplicación frontend no cambió desde ese árbol. El rewrite Vercel se inspeccionó estáticamente, no se desplegó. |

La suite de 372 pruebas se ejecutó tras integrar dos commits nuevos en `origin/main`: configuración Resend con Anymail y backend Gmail API. Las credenciales y envíos reales siguen sin verificarse. Las pruebas incluyen dobles/mock donde corresponde; no son transacciones reales ni un recorrido E2E.

## Pruebas manuales

Los cuatro casos preparados por Vicente permanecen **pendientes** de ejecución manual de Ismael: catálogo/carrito, pasarela Webpay, pago exitoso y descarga. Los pasos exactos y las precondiciones están en [guía manual de Ismael](qa/GUIA_EJECUCION_MANUAL_ISMAEL.md); el [registro](qa/REGISTRO_EJECUCION_VICENTE.md) reserva una fila por caso. Los pagos requieren integración oficial TEST y autorización de Felipe. No se ejecutó ni automatizó una compra, y no se usaron credenciales financieras reales.

## Límites

No se probó transacción real/sandbox de Webpay, operación R2, Gmail API, Resend, SMTP, Firefox manual, compra/descarga E2E ni despliegue externo. El código de integración no acredita cuenta configurada ni entrega del servicio. La ejecución automatizada se atribuye al runner, no a Vicente ni a Ismael. El diseño de casos se atribuye a Vicente según las evidencias disponibles; no se recuperó su DOCX original de E2E.

## Reproducibilidad y seguridad

En el worktree aislado: `scripts/qa/setup.sh` si hace falta crear el entorno, `scripts/qa/start.sh`, `scripts/qa/verify.sh`; detener con `scripts/qa/stop.sh`. El setup usa solo PostgreSQL `127.0.0.1:55433–55499`, DB/volumen propios y `media/qa`. No copiar `.env.qa` al repositorio ni snapshot. Los casos externos se ejecutan solo con cuentas de prueba y autorización; no poner secretos en archivos ni evidencias.
