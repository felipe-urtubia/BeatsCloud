# Product Backlog — inventario técnico inicial

**Estado:** borrador derivado del código y registro de cambios; no es export ni sustituto de Jira.
**Corte:** 12-11-2026. **Sprint 3:** 12–15 nov.; **Sprint 4:** 16–19 nov. (fechas informadas).

Las prioridades y asignaciones no se inventan. Ordenar y vincular cada fila con la clave Jira vigente antes de comprometer alcance de sprint. Los criterios son comprobables, pero deben cotejarse con los tickets oficiales.

| ID local | Capacidad / resultado | Estado según código/evidencia | Criterio de aceptación verificable | Sprint / prioridad / responsable |
|---|---|---|---|---|
| BL-01 | Sesiones, registro, activación y CSRF | Implementación presente; existen pruebas backend registradas en `docs/evidencias/pruebas_backend.txt` e integración documentada. Activación SMTP real no acreditada. | Cuenta activada inicia sesión; endpoints privados rechazan anónimo; cierre limpia datos privados de SPA. | Confirmar en Jira |
| BL-02 | Catálogo y detalle | Implementado en React/API; smoke de lectura documentado. | Consultar catálogo real y abrir detalle; comprobar datos devueltos contra servidor. | Confirmar en Jira |
| BL-03 | Carrito y totales | API del servidor calcula subtotal/IVA/total; consta en integración backend. | Agregar pista de prueba, comprobar importes servidor/SPA y que una mutación no autorizada se rechaza. | Confirmar en Jira |
| BL-04 | Inicio y retorno de Webpay | Integración y pruebas simuladas de retorno documentadas; pago de extremo a extremo real pendiente. | En TEST, aprobar y verificar retorno/estado; rechazar/cancelar y comprobar que no se registra compra. Guardar evidencia saneada. | Confirmar en Jira |
| BL-05 | Biblioteca y descarga autorizada | Ruta/API autorizada implementada; verificaciones previas documentadas, pero evidencia solicitada para entrega falta. | Compra autorizada aparece en biblioteca y descarga produce el archivo esperado; usuario sin autorización es rechazado. | Confirmar en Jira |
| BL-06 | Carga de audio y metadata | Backend y SPA presentes; estado y disponibilidad deben verificarse en modo híbrido. Cambio local de carga aún no publicado al corte. | Subir un archivo de prueba válido, comprobar metadatos/registro en backend y error legible ante archivo no válido. | Confirmar en Jira |
| BL-07 | Reproductor y visualización | `audioEngine.ts` modificado localmente, pendiente validación real en navegador. | Probar play/pausa, cambio de pista, volumen, tiempo, visualizador y errores de origen en navegador soportado; registrar versión y evidencia. | Sprint/alcance por acordar |
| BL-08 | Perfiles, favoritos y comentarios | Componentes/API presentes; validar los criterios y permisos con tickets. | Operaciones autenticadas respetan propiedad/permisos y muestran estado persistido al recargar. | Confirmar en Jira |
| BL-09 | Entrega documental y E2E | Evidencia E2E no encontrada; documentos de inicio/visión/arquitectura/pruebas/riesgos preparados como borradores en esta carpeta. | Cada documento tiene fuente/fecha; cada captura corresponde a ejecución real sin datos sensibles; pendientes están asignados. | APT 19-11; confirmar en Jira |

## Conciliación requerida con Jira

1. Exportar épicas e historias activas, claves, prioridad, estado, responsable, sprint y criterios aceptados.
2. Mapear filas BL-01–BL-09 a claves Jira; eliminar filas duplicadas y ajustar texto al ticket.
3. Confirmar Sprint 3/4, alcance comprometido y cambios; el repositorio solo proporciona las fechas de calendario en esta auditoría.
4. Registrar qué se terminó, quedó parcial o se excluyó, junto con la evidencia asociada.
