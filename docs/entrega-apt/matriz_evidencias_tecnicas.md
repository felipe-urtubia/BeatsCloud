# Matriz de evidencias técnicas

Corte: 18-11-2026. “Completo” se refiere a la evidencia técnica declarada para este corte, no a aprobación académica. La matriz no evalúa exposición ni reflexiones personales.

| Criterio técnico | Evidencia disponible | Ubicación | Estado | Pendiente |
|---|---|---|---|---|
| Metodología y mantenimiento | Historial Git con commits funcionales/documentales; actas no verificadas | [Historial Git](../../REGISTRO_CAMBIOS_BEATSCLOUD.md), [trazabilidad](trazabilidad_tecnica.md) | parcial | Conciliar actividades con Jira y actas verificables. |
| Arquitectura | Descripción de componentes y límites del despliegue | [Arquitectura](arquitectura.md), [modelo y almacenamiento](modelo_datos_y_almacenamiento.md) | completo | Actualizar topología productiva solo con evidencia de despliegue. |
| Modelo de datos | Modelos y migraciones 0001–0027, check de migraciones | [Modelo y almacenamiento](modelo_datos_y_almacenamiento.md), `app/models.py`, `app/migrations/` | completo | Documentar esquema desplegado si se obtiene acceso al entorno final. |
| Construcción e integración | `main` local reúne frontend, backend/R2, catálogo demo y checkpoint histórico; ramas locales iniciales convergían en el candidato | Historial local `main`; auditoría del repositorio | completo | Coordinar actualización de `origin/main` y retirar ramas remotas tras rotación y confirmación. |
| Persistencia PostgreSQL | Migraciones aplicadas en DB local aislada de demostración | [Validación](validacion_tecnica_corte_2026-11-18.md) | completo | No acredita base productiva. |
| Almacenamiento local | Catálogo y audio demo locales; lectura/descarga owner y preview HTTP verificadas | [Validación](validacion_tecnica_corte_2026-11-18.md), corte 18-11-2026 | parcial | Reproducción en navegador y regresión de compra. |
| Almacenamiento R2 | Implementación y suite mock; credenciales no configuradas | [Modelo y almacenamiento](modelo_datos_y_almacenamiento.md), `app/test_r2_*.py` | parcial | Prueba real controlada con bucket de desarrollo autorizado. |
| Validación de audio/metadata | Código de validación, FFmpeg y tests relacionados | `app/audio_utils.py`, `app/metadata_validation.py`, tests Django | parcial | Evidencia manual de subida completa y audio en Firefox. |
| Webpay | Checkout/reconciliación implementados; tests con doubles | `app/webpay_reconciliation.py`, tests Webpay | parcial | E2E explícita en ambiente TEST sin credenciales reales de producción. |
| Autenticación/autorización | Sesión/CSRF; HTTP login local y 403 anónimo para full/download | [Validación](validacion_tecnica_corte_2026-11-18.md), corte 18-11-2026 | parcial | Compra post-pago entre usuarios aún requiere E2E. |
| Pruebas automatizadas | Django 367 tests; frontend 3 suites; lint y build aprobados | [Registro de validación](validacion_tecnica_corte_2026-11-18.md) | completo | Las suites mock no prueban servicios externos ni navegador. |
| Calidad del software | `pip check`, `manage.py check`, migraciones, TypeScript y build | [Registro de validación](validacion_tecnica_corte_2026-11-18.md), 18-11-2026 | completo | No acredita despliegue, proveedores externos ni E2E de navegador. |
| Mejoras técnicas trazables | Commits feature y tests correlacionados por ruta/fecha | [Trazabilidad](trazabilidad_tecnica.md), historial Git | parcial | Vincular issues Jira mediante export accesible y validar defectos/cierres. |
| Contribuciones técnicas individuales | Autores y merges Git observables, con límites de atribución | [Trazabilidad](trazabilidad_tecnica.md) | parcial | Confirmar identidad de alias y actividades no reflejadas en Git. |
| Evidencia técnica versionada | Documentación, pruebas y migraciones comprometidas localmente; sin publicar el corte saneado | `docs/entrega-apt/`, `app/test_*.py`, commits locales en `main` | parcial | Publicar solo tras completar rotación/revocación y revisión coordinada. |
| Revisión de secretos/publicación | `agregar.html`/`agregar.zip` no aparecen en el árbol ni commits alcanzables locales tras `git-filter-repo` 2.47.0; GitHub aún conserva refs antiguas | Auditoría local `main`; rutas históricas retiradas del grafo local | parcial | Custodios deben confirmar rotación/revocación; después coordinar saneamiento remoto, PR #2 y ramas. No se afirma que credenciales estén rotadas. |
