# Registro de ejecución QA

Registro de los cuatro casos diseñados por Vicente. Los pasos completos están en [GUIA_EJECUCION_MANUAL_ISMAEL.md](GUIA_EJECUCION_MANUAL_ISMAEL.md). No existen resultados manuales aprobados. Registrar por separado diseño, ejecutor y herramienta: Vicente es diseñador; Ismael figura como ejecutor pendiente; automatización identifica runner sin atribución manual. No completar resultados antes de ejecutar. Adjuntar evidencia sin cookies, tokens, datos personales ni credenciales.

| Fecha/hora | Versión/commit | Entorno/navegador | ID de caso | Resultado | Evidencia/ubicación | Observaciones | Defecto asociado | Responsable | Estado de resolución |
|---|---|---|---|---|---|---|---|---|---|
| Pendiente | Registrar SHA de ejecución | Firefox local/Linux | QA-VIC-01 Catálogo y carrito | Pendiente | Guía; añadir captura saneada tras ejecutar | Diseño Vicente; ejecución Ismael pendiente | — | Ismael al ejecutar | Pendiente |
| Pendiente | Registrar SHA de ejecución | Firefox local / Transbank TEST | QA-VIC-02 Pasarela Webpay | Bloqueado sin credenciales/autorización TEST | Guía; adjuntar solo evidencia redactada | No usar LIVE; redirección no acredita compra | — | Ismael al ejecutar | Pendiente |
| Pendiente | Registrar SHA de ejecución | Firefox local / Transbank TEST | QA-VIC-03 Pago exitoso | Bloqueado hasta sandbox autorizado | Guía; adjuntar confirmación backend saneada | Manual en sandbox; no automatizar compras | — | Ismael al ejecutar | Pendiente |
| Pendiente | Registrar SHA de ejecución | Firefox local / DB QA | QA-VIC-04 Descarga del archivo | Bloqueado hasta compra QA aprobada | Guía; adjuntar metadata/captura saneada | No sembrar compras manualmente en DB | — | Ismael al ejecutar | Pendiente |

## Formato de reporte de defecto

```text
Título:
Prioridad (P0–P3) y severidad (bloqueante/alta/media/baja):
Fecha/hora:
Entorno y navegador:
Versión/commit:
Rol usado (sin incluir credenciales):
Precondiciones/datos:
Pasos numerados para reproducir:
Resultado esperado:
Resultado actual:
Frecuencia (siempre/intermitente/una vez; cantidad de intentos):
Evidencia (ruta/captura/log redactado):
ID de caso QA:
Estado (nuevo/en análisis/corregido/verificado/cerrado):
Responsable asignado por el equipo:
```
