# Inicio del proyecto — BeatsCloud

**Estado:** borrador para validación del equipo
**Fecha de corte:** 12-11-2026
**Entrega APT prevista:** 19-11-2026

## Propósito

BeatsCloud es una aplicación web para que productores publiquen pistas y para que artistas/usuarios puedan descubrirlas, reproducir previews, gestionar un carrito y acceder a compras/licencias. El repositorio contiene una SPA React/TypeScript y un backend Django que entrega páginas tradicionales y una API JSON consumida por la SPA.

## Problema y usuarios

La solución implementa un catálogo de pistas y perfiles musicales con flujos de cuenta, publicación, compra y descarga controlada. Los roles de dominio observables en `app/models.py` son artista y productor; Django mantiene además la identidad de usuario.

La formulación del problema de negocio, los segmentos prioritarios, el patrocinador/cliente y las métricas de éxito no están acreditados por los archivos consultados. El equipo debe completarlos con el acta o definición aprobada, sin inferirlos del código.

## Alcance técnico visible

- Catálogo, búsqueda, filtros/orden en cliente, detalle de pista, perfiles, favoritos/comentarios.
- Registro, activación por correo, login/logout mediante sesión Django y protección CSRF.
- Carga/edición de pistas y metadatos; disponibilidad depende del modo configurado y del servicio backend.
- Carrito y totales calculados por el servidor.
- Integración de inicio/confirmación Webpay Plus y registro de transacciones; el código y las pruebas automáticas no prueban por sí mismos un recorrido real con simulador.
- Historial de compras y endpoint de descarga con autorización backend.
- Modo `mock` de demostración separado de `hybrid` (API Django), según `frontend/client/.env.example`.

## Límites y dependencias

La aceptación de la entrega requiere entorno accesible, configuración local de secretos, servicio de correo para activar cuentas, datos de prueba no personales, archivo de audio de prueba y credenciales oficiales de Webpay TEST si se ejecuta la pasarela. No se deben incluir credenciales en Git ni capturas con información identificable.

La descarga autorizada se describe como entrega del archivo de audio asociado a la pista; el repositorio no acredita entrega separada de stems. No se presenta como DRM.

## Hitos informados

| Hito | Fecha | Estado al corte |
|---|---|---|
| Sprint 3 | 12–15-11-2026 | Calendario informado; objetivo y resultado deben confirmarse en Jira/equipo. |
| Sprint 4 | 16–19-11-2026 | Calendario informado; objetivo y resultado deben confirmarse en Jira/equipo. |
| Entrega APT | 19-11-2026 | Fecha prevista informada por el equipo. |

## Aprobaciones por completar

Registrar nombre/rol y fecha de quien valida alcance, visión, backlog, criterios de aceptación, arquitectura de despliegue y resultado de cada Review. No hay nombres de responsables confirmados en las fuentes disponibles.
