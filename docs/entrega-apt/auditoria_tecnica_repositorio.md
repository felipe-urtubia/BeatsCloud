# Auditoría técnica del repositorio BeatsCloud

**Corte:** 18-11-2026. **Repositorio:** `felipe-urtubia/BeatsCloud`. **Rama de trabajo auditada:** `main` local tras consolidar contribuciones disponibles y filtrar rutas sensibles. Esta es una auditoría de implementación y evidencia; no certifica producción ni servicios de terceros.

## Resultado ejecutivo

El candidato integra `frontend-trabajo` con `origin/main` y contiene backend Django, SPA React, migraciones R2/Webpay, pruebas, documentación técnica y el comando local de catálogo demo. La base aislada y el catálogo funcionan localmente; suites automatizadas de backend/frontend, chequeo TypeScript, build y verificaciones de Django aprobaron en el corte.

La integración local no debe publicarse todavía. `origin` es público y GitHub conserva las ramas e historia antiguas con `agregar.html`, ZIP cuyo único miembro era `.env` con campos sensibles no vacíos. `git-filter-repo` 2.47.0 retiró las rutas de todas las referencias locales; las ramas remotas aún no se modificaron. La rotación/revocación externa no está confirmada. El commit integrado tras filtrar es `31796c2`; la limpieza de referencias locales continúa.

## Arquitectura observada

- **Frontend:** React 19, TypeScript, Vite 6 y Tailwind. El cliente `frontend/client/src/api/django.service.ts` implementa solicitudes JSON/multipart, cookies de mismo origen y token CSRF; `AppContext.tsx` orquesta catálogo, perfil, sesión, carrito, pagos y carga. Vite configura proxy local de `/api` y `/media` a Django.
- **Backend:** Django 6.0.6, vistas HTML y API JSON propia en `app/api_shim.py`; no se usa Django REST Framework. `beatcloud/urls.py` combina las rutas de la SPA/API con rutas tradicionales.
- **Persistencia:** PostgreSQL; modelos Django y 27 migraciones de `app`. La demostración se validó en una base local aislada, no en una base productiva.
- **Identidad:** autenticación de Django por sesión, cookie y CSRF. Las rutas mutables validan CSRF; las rutas de audio completo/descarga aplican controles de sesión/propiedad/compra.
- **Configuración segura:** `DJANGO_SECRET_KEY` ahora falla al faltar; `DEBUG` por defecto es falso y `DB_PASSWORD` por defecto vacío. `.env.example` deja la clave vacía y no contiene credenciales de proveedor.
- **Audio:** almacenamiento local con `FileField` y `MEDIA_ROOT` o R2 cuando está configurado. FFmpeg genera preview MP3; el catálogo expone preview y separa la ruta del original.
- **R2:** módulos para presign, confirmación, registro, claims, preview, claves privadas, autorización y enlaces temporales. En el entorno auditado no había configuración R2 utilizable; tests de R2 usan mocks. No se comprobó una cuenta real de Cloudflare.
- **Webpay:** Transbank SDK y servicio de conciliación backend; la suite simula proveedor/respuestas. El `.env` declara modo TEST, pero no se ejecutó transacción externa.

## Persistencia y media

`Usuario` enlaza uno-a-uno con `auth.User` y distingue artista/productor. `Track` se relaciona con `Genero_Musical` y `Usuario`; guarda precio, metadatos D9, audio, preview, portada, backend de almacenamiento y estado de media. `WebpayTransaction` identifica orden/token y conserva estado, monto y snapshot; `R2UploadClaim` reserva y asocia cargas. La descripción de atributos, claves y migraciones está en [modelo de datos y almacenamiento](modelo_datos_y_almacenamiento.md).

Las migraciones de `app` llegan a `0027_track_r2_owner_user_id`. En PostgreSQL local de demo se aplicaron; `makemigrations --check --dry-run` reportó que no hay cambios pendientes. Los cinco beats demo tienen WAV original local, preview MP3 y portada. No se cargaron archivos a R2.

## Validación

Resultados reproducibles y limitaciones detalladas: [validación técnica 18-11-2026](validacion_tecnica_corte_2026-11-18.md). Se ejecutaron Django (367 pruebas), frontend (26 tests en tres archivos/suites), lint TypeScript (`tsc -b`), build Vite, `pip check`, `manage.py check` y verificación de migraciones. En HTTP local se validaron catálogo, sesión, CSRF/login, preview, 403 anónimo de audio completo/descarga y entrega autenticada del propietario.

No se validó reproducción audible en navegador, compra E2E como comprador distinto, Webpay contra Transbank, R2 contra Cloudflare ni rendimiento de WAV/stems. Un HTTP 200 de una ruta no acredita el flujo completo.

## Ramas, PR y contribuciones

La auditoría inicial encontró seis ramas locales y tres remotas (`main`, `frontend-trabajo`, `integration/react-frontend`). Todas las ramas locales apuntaban a commits contenidos en el candidato consolidado. `main` local incluye `frontend-trabajo`, la antigua `origin/main` y cuatro commits de `integration/reorganization-checkpoint` (`9f4f85b`, `de4a79a`, `a907e41`, `53db43f`) como ascendencia de un merge `ours`; su árbol `client/`/`server/` reemplazaría módulos y migraciones R2 actuales, así que se conserva el árbol vigente. Los OID cambiaron al retirar las rutas sensibles; hashes anteriores solo identifican antecedentes históricos.

GitHub: PR #1 (React/Django) MERGED, autor de GitHub `yaeaelo` (Ismael Araya); PR #3 (descarga R2 temporal) MERGED, autor `felipe-urtubia`; PR #2 desde `frontend-trabajo` sigue OPEN y corresponde a cambios ya integrados en el candidato. No tiene reviews ni comentarios visibles. Jira no está conectado.

La [trazabilidad técnica](trazabilidad_tecnica.md) distingue commits, autoría Git/GitHub e integración. No se encontró evidencia Git/GitHub enlazada a Vicente Monroy; esto no prueba ausencia de pruebas o trabajo, solo limita la atribución verificable.

## Hallazgo de seguridad: `agregar.html`

No es una página referenciada por código: la búsqueda en código no encontró usos; las menciones restantes documentan el riesgo. El árbol integrado lo eliminó y `.gitignore` ahora ignora `/agregar.html` y `/agregar.zip`.

Historial inspeccionado, sin extraer ni mostrar valores:

| Referencia histórica | Ruta en el commit | Metadatos del ZIP |
|---|---|---|
| `adbab4f` (28-08-2026; hash previo al filtrado, commit eliminado) | `agregar.zip` | Un miembro `.env.example`. |
| `28864ca` (29-08-2026; hash previo al filtrado, commit eliminado) | `agregar.html` (rename) | Un miembro `.env.example`. |
| `bb7533c` (equivale a `497d5ac` previo al filtrado) y descendientes | `agregar.html` | Un miembro `.env`; contenía valores no vacíos en campos sensibles. La ruta fue retirada de los commits actuales. |
| `9f4f85b` (equivale a `a1294b9` previo al filtrado; fecha 06-11-2026) | `agregar.html` | Eliminado de ese árbol. |
| `ec00e2e` (17-11-2026; hash previo al filtrado, commit eliminado) | `agregar.html` | Reintroducido como ZIP con un miembro `.env`; el commit quedó eliminado de la historia local reescrita. |

Antes del filtrado no se encontraron otros nombres de archivos `.env`, SQLite, claves PEM o claves SSH en los objetos rastreados; sí existen `.env.example`. Un escaneo `detect-secrets` 1.5.0 revisó 569 blobs de texto alcanzables y los miembros `.env` archivados sin emitir hallazgos heurísticos. Ese resultado no invalida el hallazgo directo de variables sensibles con valores no vacíos. La inspección post-filtrado no encontró `agregar.html`/`agregar.zip` entre los objetos alcanzables locales; la verificación final se registra tras limpiar refs.

Variables que requieren confirmación de rotación/revocación por los custodios: `DJANGO_SECRET_KEY`, `EMAIL_HOST_PASSWORD`, `TRANSBANK_API_KEY`, `DB_PASSWORD`, `R2_ACCESS_KEY_ID` y `R2_SECRET_ACCESS_KEY`. Revisar además sesiones firmadas, actividad SMTP/Transbank, cuenta/rol DB y accesos R2. `TRANSBANK_COMMERCE_CODE`, `R2_ACCOUNT_ID`, `R2_BUCKET_NAME`, `EMAIL_HOST_USER` y `DB_USER` son identificadores/configuración expuestos que requieren revisión, no necesariamente rotación. En las versiones examinadas `TRANSBANK_SHARED_SECRET` y `STRIPE_SECRET_KEY` estaban vacías; no se afirma exposición de esos valores. **La rotación no está confirmada.**

## Estado documental y de publicación

La matriz técnica y los documentos de arquitectura, datos, almacenamiento, pruebas y trazabilidad están enlazados desde [README técnico](README.md). Los documentos con corte 12-11 conservan su fecha y alcance histórico; no se actualizan retrospectivas/reviews sin actas. Las capturas y E2E de navegador siguen pendientes.

El repositorio GitHub es público, el default branch es `main`, el token consultado tiene permiso WRITE y no se observó protección de rama habilitada. PR #2 sigue abierto; eliminar su head branch antes de cerrar/concluir la incidencia rompería su referencia. No se enviaron mensajes al equipo ni se ejecutaron operaciones remotas destructivas. La reescritura y publicación requieren confirmar primero la rotación de credenciales y coordinar a quienes usan las ramas antiguas.
