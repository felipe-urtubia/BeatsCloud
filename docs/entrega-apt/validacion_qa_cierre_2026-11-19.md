# QA de cierre — 19-11-2026

**Producto probado:** `ee981a750904b4263b20be2f91e3568c0e1699ea`. Ejecución local aislada en worktree limpio; PostgreSQL de QA separado y base temporal de Django eliminada al finalizar. R2 permaneció desactivado, Webpay sin credenciales y correo de QA en memoria/consola. No se contactaron servicios externos.

| Comprobación | Resultado |
|---|---|
| `manage.py check` | OK. |
| `makemigrations --check --dry-run` | OK; sin cambios de migración. |
| `manage.py test` | **372/372 aprobadas.** |
| `npm test` | **26/26 aprobadas.** |
| `npm run lint` | OK (`tsc -b`). |
| `npm run build` | OK; Vite transformó 1.926 módulos. |

Estos resultados pertenecen a una sola ejecución en el SHA integrado. No son prueba de proveedores externos, despliegue ni compra completa.

## Evidencia separada de otros cortes

- `4569613b29e7023161149ca5e7d5fddabf6437db`: `bash build.sh`, `collectstatic`, `manage.py check`, migraciones y smoke HTTP en base QA aislada. El catálogo devolvió HTTP 200 y el registro de esa ejecución observó 125 pistas.
- `validacion_tecnica_corte_2026-11-18.md`: HTTP local para preview, sesión y permisos de audio completo/descarga.
- La prueba de navegador Selenium del 19-11 se conserva en el anexo académico. Comprobó catálogo/carrito con datos sintéticos; abrió la confirmación local, pero no inició Webpay ni validó retorno, compra o descarga. Fue automatizada, no manual.

## Funcionalidad e integraciones

Felipe confirmó que el equipo probó funcionalmente registro/activación, recuperación/cambio de contraseña y eliminación de cuentas con el proveedor de correo configurado. Esta confirmación corresponde al equipo; la ejecución local arriba no envió mensajes externos.

El código integra URL firmada para subida R2, carga directa desde frontend, confirmación/finalización en backend y URL firmada de descarga expirable. En el corte original del 19-11-2026 no se acreditaron pruebas externas contra R2 ni Webpay. Las validaciones posteriores del 22-11-2026 verificaron persistencia R2, despliegue en Render y Vercel, y compra/descarga E2E mediante Webpay TEST. Las pruebas de usabilidad con usuarios externos y carga cloud permanecen sin acreditar.

## Reproducir suites localmente

Con dependencias y PostgreSQL local configurados mediante archivos `.env` privados:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
cd frontend/client
npm ci
npm test
npm run lint
npm run build
```

No versionar `.env` ni `.env.qa`; `.env.example` contiene solo claves y valores de ejemplo.


## Seguimiento de almacenamiento R2 - 22-11-2026

| Comprobación | Resultado |
|---|---|
| Pruebas Django de los cambios de previews | 405/405 aprobadas |
| Comprobación Django | OK |
| Cambios pendientes de migración | Ninguno |
| Build React/Vite | OK |
| Conexión PostgreSQL de producción | Verificada |
| Originales existentes en R2 | 3/3 |
| Recuperación de previews | 3/3 |
| Auditoría posterior | 3 correctas, 0 pendientes, 0 con problemas |
| Reproducción con el nuevo despliegue | Verificada con y sin sesión |
| Subida nueva con persistencia R2 | Verificada |

Esta validación es independiente del corte original del
19-11-2026. No acredita cobros reales ni certificación comercial de Webpay. La compra y descarga E2E en el ambiente TEST fueron verificadas posteriormente el 22-11-2026.

## Actualización QA - 22-11-2026: Webpay TEST y permisos de audio

Validación funcional en Render, Vercel, PostgreSQL y Cloudflare R2.

| Caso de prueba | Resultado |
|---|---|
| Webpay TEST: pago aprobado | Correcto |
| Registro de compra en PostgreSQL | Correcto |
| Descarga y reproducción del original | Correcto |
| Webpay TEST: pago rechazado | Correcto |
| Pago rechazado sin nueva compra | Correcto |
| Acceso anónimo al original | HTTP 403 |
| Acceso autenticado sin compra | HTTP 403 |
| Acceso autenticado con compra | HTTP 200 |
| Preview y sincronización de reproductores | Correcto |
| Pruebas automatizadas frontend | 33/33 |
| TypeScript y build Vite | Correcto |

Commits de referencia:

- `4d97b99`: profesionalización de mensajes visibles.
- `c029e0d`: sincronización de duración y progreso del audio.

La validación corresponde al ambiente de integración de Transbank,
sin cobros reales. No acredita certificación comercial LIVE,
pruebas de carga ni usabilidad con usuarios externos.

Detalle: [Registro histórico de cambios](../../REGISTRO_CAMBIOS_BEATSCLOUD.md).
