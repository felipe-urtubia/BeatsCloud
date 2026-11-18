# Inicio del proyecto — BeatsCloud

**Documento de trabajo; no aprobado por patrocinador ni cliente.**
**Corte documental:** 12-11-2026 · **Presentación APT prevista:** 19-11-2026

## Antecedentes y contexto

BeatsCloud es un proyecto académico de aplicación web para catálogo y comercialización de pistas musicales. El repositorio documenta una evolución desde una aplicación Django con plantillas hasta una arquitectura que también ofrece una SPA React/TypeScript y una API JSON de Django. El registro de cambios cubre trabajo entre agosto y noviembre de 2026; la integración real del frontend y el modo de demostración están descritos en `docs/INTEGRACION_BACKEND.md`.

El proyecto contempla artistas/compradores, productores y visitantes. Los modelos de `app/models.py` establecen los tipos de perfil Artista y Productor; la identidad y las sesiones pertenecen a Django.

## Problema que aborda

El producto implementa un lugar donde un productor puede publicar pistas y un artista puede descubrirlas, escuchar una muestra, agregarlas a un carrito y, sujeto a autorización del pago, acceder a su historial y al archivo adquirido. Esta formulación se deriva de las capacidades implementadas y de las rutas existentes; la definición aprobada del problema de negocio, su contexto de mercado y la necesidad expresada por un cliente no están en las fuentes consultadas.

## Objetivos

### Objetivo general

Implementar y documentar una aplicación web que conecte la publicación y descubrimiento de pistas con un flujo controlado de compra y acceso a archivos, con Django como autoridad para identidad, persistencia y autorización.

### Objetivos específicos derivados del producto

1. Permitir administrar perfiles y publicar pistas con metadatos de audio.
2. Permitir explorar catálogo, perfiles y detalles de pistas.
3. Mantener autenticación por sesión de Django y protección CSRF en operaciones mutables.
4. Calcular el carrito en el servidor e integrar la creación/confirmación de pagos Webpay.
5. Registrar compras autorizadas y restringir la descarga al comprador habilitado.
6. Distinguir claramente la demo local (`mock`) de la integración con backend (`hybrid`).

Estos son objetivos técnicos reconstruidos del código, no una transcripción de un acta de inicio aprobada.

## Alcance y exclusiones

### Incluido en el producto del repositorio

- SPA React y vistas web Django.
- Registro, activación por correo, login/logout, sesión y CSRF.
- Perfiles de artista/productor, catálogo, búsqueda/filtros, detalle, likes y comentarios.
- Publicación/edición de pistas, metadatos, previews y recursos audiovisuales.
- Carrito, precios/totales de servidor, integración Webpay Plus y estado de transacción.
- Historial de compra y endpoints protegidos de reproducción/descarga.
- Modo `mock` para demostración sin persistencia real y modo `hybrid` para conexión con Django.
- Entrega documental APT y evidencia de ejecución, cuando esta última se produzca realmente.

### Fuera del alcance acreditado

- Operación en producción, disponibilidad, monitoreo, hosting o topología productiva.
- DRM o distribución de stems independientes; el backend entrega el archivo asociado al track.
- Afirmar una pasarela Stripe operativa: se encuentran variables/configuración, pero no hay evidencia suficiente de un flujo Stripe activo.
- Declarar realizado el pago E2E TEST hasta contar con ejecución y evidencia del recorrido completo.

## Usuarios y actores

| Actor | Interacción que respalda el código | Estado documental |
|---|---|---|
| Visitante | Consulta catálogo y perfiles públicos; escucha previews disponibles. | Implementado en código; validación E2E del corte pendiente. |
| Productor | Administra perfil y publica/edita sus pistas. | Implementación backend/frontend presente; carga híbrida requiere validación reciente. |
| Artista/comprador | Explora pistas, gestiona carrito, revisa compras y solicita descargas. | Flujos implementados; pago/retorno/descarga E2E del corte pendientes. |
| Django/backend | Autoridad de sesión, roles, datos, precios, transacciones y autorización. | Implementado; existen pruebas y verificaciones históricas citadas en el plan de pruebas. |
| Transbank/Webpay | Servicio externo de pago. | Integración de software presente; operación con simulador real pendiente de evidencia. |
| Equipo académico / evaluador | Revisa producto y entrega APT. | Evaluación prevista; nombres y criterios formales no disponibles. |

## Equipo y responsabilidades

Las fuentes consultadas no proporcionan una lista confirmada de integrantes, roles, Product Owner, Scrum Master ni asignación por componente. Vicente es mencionado como persona que informó sobre el documento E2E; no se infiere que sea responsable de pruebas. Completar la matriz solo con confirmación directa.

| Responsabilidad | Persona confirmada | Acción de validación |
|---|---|---|
| Patrocinador/cliente o Product Owner | No disponible | Equipo debe confirmar nombre, rol y aprobación de visión/backlog. |
| Coordinación del proyecto | No disponible | Confirmar en acta/Jira. |
| Desarrollo frontend/backend | No asignado en fuentes consolidadas | Confirmar participantes y autoría por sprint. |
| QA/evidencia E2E | No disponible | Designar ejecutor, cuenta y entorno de prueba. |
| Seguridad/credenciales | No disponible | Designar responsables autorizados para rotación y saneamiento del archivo heredado. |

## Metodología y gestión

El material del equipo usa sprints, tickets DDPB y verificaciones por hitos. Se adopta aquí únicamente el hecho de que existe trabajo organizado por sprint; no se califica el proceso como Scrum formal ni se inventan ceremonias. El Product Backlog oficial, estimaciones, Definition of Done, objetivos de sprint y asignaciones requieren export/confirmación de Jira, que no está disponible en esta sesión.

## Tecnologías y herramientas observables

- Backend: Python y Django 6.0.6 (versión de `requirements.txt`), app `app`, API JSON propia en `app/api_shim.py` y plantillas Django.
- Frontend: React 19, TypeScript 5.7, Vite 6, Tailwind CSS 4 y `lucide-react` (`frontend/client/package.json`).
- Datos: PostgreSQL es el motor configurado y validado en este corte. Aunque `DB_ENGINE` se lee desde el entorno, el `OPTIONS` actual contiene parámetros específicos de PostgreSQL; SQLite no se documenta como backend local compatible. No se conoce qué motor corresponde a un ambiente de evaluación.
- Archivos: almacenamiento Django bajo `MEDIA_ROOT` en el entorno configurado; audios/imágenes y previews. No se acredita almacenamiento remoto durable.
- Autenticación: sesiones Django y CSRF; no JWT para la SPA.
- Integración externa: SDK `transbank-sdk` para Webpay Plus y SMTP configurable para activación/recuperación de cuenta.
- Herramientas de validación del audio: `mutagen` y configuración FFmpeg.
- Repositorio y pruebas: Git, pruebas Django y pruebas frontend con Node `node:test`; ambiente de navegador necesario para E2E/audio.

## Planificación informada

| Periodo | Fechas | Estado al corte 12-11-2026 | Fuente/confirmación pendiente |
|---|---|---|---|
| Sprint 1 | Fechas no verificadas | Historial/acciones aludidos en registro; acta no encontrada. | Recuperar Jira y acta de inicio/review/retro. |
| Sprint 2 | Se localizó verificación técnica fechada 05-11-2026 en otra rama local | Verificación técnica histórica, no acta oficial de Review/Retrospectiva. | Contrastar commits, alcance y tickets con Jira. |
| Sprint 3 | 12–15-11-2026 | En curso según calendario informado; no redactar resultados por adelantado. | Confirmar objetivo y compromiso en Jira. |
| Sprint 4 | 16–19-11-2026 | Futuro al corte; no redactar resultados por adelantado. | Confirmar objetivo y compromiso en Jira. |
| Presentación APT | 19-11-2026 | Fecha prevista por el equipo. | Confirmar horario, rúbrica y entregables exigidos. |

## Restricciones, dependencias y supuestos

- Acceso al ambiente `hybrid`, base de datos de prueba, medios de prueba permitidos y sesión activada.
- La activación requiere un backend de correo configurado; para pruebas locales se puede usar el backend de consola configurado por el equipo.
- Pago E2E requiere confirmar el endpoint y credenciales oficiales de Webpay TEST sin exponerlas.
- Catálogo, carrito y compra deben probarse con datos ficticios y sin alterar compras reales.
- Capturas no pueden exponer datos personales, secretos, cookies, tokens, tarjetas ni metadatos privados.
- `agregar.html` fue retirado del árbol de integración después de inspeccionar solo el listado del ZIP, que contiene un miembro `.env`; no se extrajo. El blob permanece en el historial Git y requiere respuesta de seguridad antes de publicar.
- El documento E2E referido por el equipo no se encontró en el árbol visible; ubicación y versión original deben confirmarse antes de sustituirlo.

## Pendiente de validación del equipo

Confirmar el problema de negocio en palabras del usuario/cliente, objetivos aprobados, patrocinador, integrantes/roles, metodología formal, objetivos y compromisos de cada sprint, plataforma/DB del ambiente de demo, rúbrica APT, exclusiones acordadas y aceptación de este documento. No se completan nombres ni aprobaciones por inferencia.

## Fuentes

- [README del proyecto](../../README.md)
- [Registro de cambios](../../REGISTRO_CAMBIOS_BEATSCLOUD.md)
- [Integración backend](../INTEGRACION_BACKEND.md)
- `app/models.py`, `app/api_shim.py`, `app/urls.py`, `beatcloud/settings.py`
- `frontend/client/package.json`, `frontend/client/src/context/AppContext.tsx`, `frontend/client/src/api/django.service.ts`
