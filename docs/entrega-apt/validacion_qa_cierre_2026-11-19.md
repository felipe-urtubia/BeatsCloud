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

El código integra URL firmada para subida R2, carga directa desde frontend, confirmación/finalización en backend y URL firmada de descarga expirable. No hay evidencia de bucket R2 real, persistencia cloud ni descarga desde infraestructura. Webpay Plus está implementado y tiene pruebas automatizadas con dobles, pero no hay transacción TEST real ni compra/descarga E2E acreditada. Tampoco se acredita despliegue externo, pruebas de usabilidad con usuarios externos ni carga cloud.

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
| Reproducción con el nuevo despliegue | Pendiente |
| Subida nueva con persistencia R2 | Pendiente |

Esta validación es independiente del corte original del
19-11-2026. No acredita una compra Webpay real ni una prueba
completa de reproducción del código pendiente de publicar.
