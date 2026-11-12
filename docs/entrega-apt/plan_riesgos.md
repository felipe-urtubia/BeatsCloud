# Plan de riesgos — entrega APT

**Corte:** 12-11-2026. Probabilidad e impacto iniciales son evaluación cualitativa para discutir, no registro aprobado por el equipo.

| ID | Riesgo / señal | Prob. | Impacto | Mitigación / contingencia | Responsable |
|---|---|---|---|---|---|
| R-01 | Falta ejecutar el pago E2E TEST y retorno Webpay antes del 19-11. | Alta | Alto | Reservar cuenta/ambiente de pruebas; ejecutar T-02–T-05; si se bloquea, mostrar el estado como pendiente y adjuntar evidencia del bloqueo. | Por asignar |
| R-02 | No se encontró `Evidencia_Pruebas_E2E_BeatsCloud.docx` ni capturas E2E en el árbol inspeccionado. | Alta | Alto | Confirmar ubicación con Vicente/equipo; conservar original y versionar evidencia saneada. | Por asignar |
| R-03 | Audio engine cambiado localmente aún no validado en navegador. | Media | Alto | Probar en navegador real con diferentes pistas/controles; mantener pendiente hasta resultado. | Por asignar |
| R-04 | Sin Jira exportado no se pueden validar prioridades, alcance ni consistencia de Sprint 3/4. | Alta | Alto | Exportar tablero y conciliación del backlog/actas antes de cerrar presentación. | Por asignar |
| R-05 | Activación depende de SMTP/cuenta; no se ha acreditado disponibilidad para demo. | Media | Alto | Preparar cuenta ficticia activada autorizada o backend de correo de desarrollo; no usar datos reales en capturas. | Por asignar |
| R-06 | `agregar.html`, ya versionado en `main`, es un ZIP que contiene `.env`, `frontend/client/.env` y `server/db.sqlite3`. La configuración del `.env` contiene valores no vacíos para variables de Django, correo, Transbank y base de datos; sus valores no se reproducen aquí. | Confirmado | Crítico | Tratar las credenciales como expuestas: responsables autorizados deben identificar/rotar credenciales, evaluar el historial y acordar saneamiento del blob antes de distribuir una copia limpia. No extraer ni volver a publicar el contenido. El commit de este PR no modifica el archivo, pero el hallazgo sigue presente en su rama base. | Por asignar |
| R-07 | Un fallo de conectividad o ambiente de prueba puede confundirse con éxito de modo mock. | Media | Alto | Identificar siempre `hybrid`/`mock` en registro y no aceptar mock para pago, persistencia o descarga autorizada. | Por asignar |
| R-08 | Entrega de audio de prueba puede contener material protegido o metadata personal. | Media | Medio | Usar recurso propio/sintético con permiso; retirar metadata privada antes de distribuir. | Por asignar |

## Revisión

En la reunión de planificación, asignar propietario y definir probabilidad/impacto usando la escala acordada por el equipo. Revisar diariamente durante Sprint 3/4 y registrar fecha, cambio, decisión y responsable. El registro actual no demuestra que esas reuniones hayan ocurrido.
