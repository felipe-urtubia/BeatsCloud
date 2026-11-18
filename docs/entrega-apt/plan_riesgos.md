# Plan de riesgos — entrega APT BeatsCloud

**Corte:** 12-11-2026 · **Estado:** evaluación inicial de documentación, no acta aprobada por el equipo.
Probabilidad/impacto son apreciaciones cualitativas para priorizar conversación; responsables de proyecto no confirmados.

## Escala de evaluación

- **Probabilidad:** Baja (poco probable con controles actuales), Media (puede ocurrir), Alta (ya existe la condición o es probable antes de la entrega).
- **Impacto:** Bajo (menor), Medio (retrasa una parte), Alto (afecta flujo/entrega), Crítico (exposición de credenciales/datos o impide distribuir el proyecto con seguridad).
- **Criticidad:** juicio combinado probabilidad × impacto; Crítica si impacto crítico, Alta para combinaciones que pueden impedir aceptación APT.
- **Estado:** Abierto hasta que exista evidencia fechada de mitigación y validación. Responsable queda “Por asignar” cuando no consta una persona.

## Registro

| ID | Riesgo | Probabilidad | Impacto | Criticidad | Mitigación y contingencia | Responsable | Estado al corte |
|---|---|---|---|---|---|---|---|
| R-01 | `agregar.html` estuvo versionado en la historia pública previa: era ZIP con un miembro `.env`; las versiones históricas contienen nombres de variables y valores no vacíos de configuración/credenciales. El ZIP no contiene SQLite según el listado inspeccionado. | Alta (condición confirmada) | Crítico | **CRÍTICA** | No extraer ni publicar valores. Tratar las credenciales potencialmente expuestas; custodios deben inventariar proveedores y rotar/revocar. Saneamiento local realizado; mantener publicación bloqueada hasta confirmar rotación y coordinar reescritura remota. | Por asignar: custodio repositorio + responsables de credenciales | Abierto; nombres afectados identificados, rotación no confirmada y las refs remotas aún exponen el historial previo. |
| R-02 | Credenciales o datos derivados de los `.env` embebidos ya pudieron quedar en historial remoto. | Alta | Crítico | **CRÍTICA** | Confirmar exposición con responsables/proveedores; rotar secretos en el servicio emisor y revisar sesiones/actividad. Eliminar el archivo de una copia de trabajo no revoca credenciales ni sanea historia. No transcribir secretos en tickets/capturas. | Por asignar: responsables de Django, Transbank, SMTP y base | Abierto; revisión/rotación no acreditadas. |
| R-03 | El flujo Webpay puede fallar o no poder demostrarse por falta de ambiente TEST, cuenta activa, configuración/callback o acceso a simulador. | Alta | Alto | **ALTA** | Reservar entorno y cuenta autorizada; comprobar ambiente antes de pago; probar aprobación, rechazo y cancelación; conservar estados observados. Si se bloquea, reportar bloqueo real y no sustituirlo por mock/doble. | Por asignar: integración/QA | Abierto; E2E no encontrada en evidencia disponible. |
| R-04 | Faltan capturas/registro del recorrido E2E y no se localizó el DOCX referido por Vicente. | Alta | Alto | **ALTA** | Confirmar con Vicente/equipo el lugar y versión del DOCX; revisar su contenido antes de añadir capturas. Usar matriz de `evidencias/e2e/README.md`; recortar/redactar datos antes de commit. | Por asignar; Vicente solo es fuente del aviso, no se infiere que sea responsable | Abierto. |
| R-05 | Carga de archivos y reproducción/audio pueden fallar con el servicio/archivo/navegador de demo, incluida la modificación `audioEngine.ts` del PR #2. | Media | Alto | **ALTA** | Ejecutar carga híbrida con fixture permitido y validar audio en navegador objetivo. Registrar codec, duración, navegador, errores y resultado. Mantener ambas capacidades como pendientes hasta evidencia. | Por asignar: frontend + QA | Abierto; audio real pendiente y carga reciente sin resultado en paquete. |
| R-06 | El almacenamiento de `MEDIA_ROOT` es filesystem configurado; persistencia/durabilidad compartida de archivos entre reinicios o nodos no está definida. | Media | Alto | **ALTA** | Confirmar ambiente de presentación, volumen/ruta persistente, respaldo, permisos y política de archivos. Preparar datos reproducibles o exhibir limitación si almacenamiento es efímero. | Por asignar: infraestructura/backend | Abierto; no hay despliegue/almacenamiento remoto acreditado. |
| R-07 | Frontend y API pueden desincronizar sesión/CSRF/origen/configuración; fallos de SMTP/DB también bloquean alta/compra. | Media | Alto | **ALTA** | Verificar misma origen/proxy, cookie/CSRF, migraciones, conexión DB y flujo de correo con cuenta ficticia antes de la demo. Mantener modo hybrid explícito y mensaje de error. | Por asignar: integración | Abierto; entorno APT no identificado. |
| R-08 | Falta acceso a Jira: backlog, prioridad, estado, responsables, criterios aceptados y alcance de Sprint 3/4 no se pueden confirmar. | Alta | Alto | **ALTA** | Integrante con acceso exporta Jira DDPB y concilia `product_backlog.md`; actualiza sprint/criterios con fuente. No presentar inventario técnico como backlog oficial. | Por asignar: administrador/Product Owner Jira | Abierto. |
| R-09 | La entrega del 19-11 puede quedar incompleta por sprints en curso/futuro al corte y ceremonias/evidencias sin actas localizadas. | Media | Alto | **ALTA** | Confirmar rúbrica/paquete, responsables y fecha de cierre; actualizar Review/retro solo tras reuniones reales; reservar tiempo para E2E y revisión de seguridad. | Por asignar: coordinación académica | Abierto. |
| R-10 | La prueba en `mock` puede confundirse con aceptación de persistencia, checkout o descarga real. | Media | Medio | **MEDIA** | En todas las capturas/registro anotar modo; modo `mock` se identifica como **SIMULADO** y se excluye de evidencia de APIs/pagos/descargas. | Por asignar: quien demuestre | Abierto hasta la presentación. |
| R-11 | Evidencias pueden revelar datos personales, derechos de audio, cookies, tokens o datos de pago. | Media | Alto | **ALTA** | Usar cuentas/datos sintéticos, audio autorizado, capturas recortadas y revisión por segunda persona; no publicar archivo descargado si no hay autorización. | Por asignar: QA + custodio de evidencia | Abierto. |

## Seguimiento

Actualizar por revisión de sprint con fecha, cambio de probabilidad/impacto, acción, responsable y evidencia. Cerrar un riesgo solo cuando la mitigación está realizada y comprobada; una intención o ticket creado no es cierre. Jira no estuvo disponible al preparar este documento.

## Pendiente de validación del equipo

Asignar propietarios reales; confirmar escala institucional, ambiente y almacenamiento, estado de rotación de secretos, decisión de saneamiento Git, acceso al simulador, disponibilidad de correo y plan de respuesta si Webpay/E2E sigue bloqueado. Los responsables de secretos deben actuar usando canales autorizados y no adjuntar valores a esta documentación.

## Fuentes

[README](../../README.md); [integración backend](../INTEGRACION_BACKEND.md); [registro de cambios](../../REGISTRO_CAMBIOS_BEATSCLOUD.md); `agregar.html` (clasificado por tipo/miembros sin extracción); `beatcloud/settings.py`; `app/models.py`; `app/views.py`; [protocolo E2E](evidencias/e2e/README.md).
