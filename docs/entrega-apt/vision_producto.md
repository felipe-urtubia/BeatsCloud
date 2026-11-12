# Visión del producto — BeatsCloud

**Estado:** borrador basado en funciones implementadas, pendiente de validación del equipo/cliente.
**Fecha de corte:** 12-11-2026

## Declaración de visión

Para productores que necesitan publicar su catálogo y artistas que buscan instrumentales, BeatsCloud ofrece un espacio web para descubrir pistas, revisar sus metadatos y gestionar el acceso a una compra. El backend conserva la autoridad sobre identidad, precios, autorización de pago y descarga; la interfaz React facilita el recorrido de catálogo y biblioteca.

La propuesta de valor comercial, público prioritario y diferenciadores frente a alternativas requieren confirmación de producto; no se deducen como hechos de la implementación.

## Personas y necesidades observables

| Rol | Necesidad cubierta por código | Evidencia en repositorio |
|---|---|---|
| Productor | Publicar/editar pistas y mantener perfil | `app/models.py`, APIs de upload/track y componentes de perfil/carga. |
| Artista/comprador | Explorar catálogo, comprar y revisar biblioteca | API de catálogo/carrito/compras y `ArtistProfilePage.tsx`. |
| Visitante | Descubrir catálogo y perfiles públicos | APIs `/api/catalogo/`, `/api/usuarios/` y componentes de catálogo. |

## Límites del producto actual

- API real Django en modo `hybrid`; `mock` es demostración y no valida persistencia ni pagos.
- Webpay está integrado con estado y validación backend, pero una compra completa con retorno real de TEST sigue pendiente de evidencia en este corte.
- La biblioteca puede ofrecer comprobante de demostración en modo no híbrido; no debe confundirse con una descarga real.
- El cambio local pendiente en `audioEngine.ts` necesita validación real en navegador; no se considera terminado.
- El repositorio no acredita operación en producción ni disponibilidad/monitorización de producción.

## Indicadores propuestos para acordar

Definir con el equipo medidas y umbrales para: completar publicación válida de una pista, encontrar pista usando catálogo, completar una compra TEST y acceder al archivo autorizado, y tasa de errores de esos recorridos. No hay objetivos numéricos aprobados en las fuentes inspeccionadas.

## Criterios de visión por validar

1. El productor puede publicar metadatos y audio válido en ambiente conectado.
2. Un visitante puede localizar una pista y consultar sus detalles.
3. Una persona autenticada puede mantener un carrito con totales calculados por servidor.
4. Solo un resultado autorizado habilita la compra y descarga correspondiente.
5. Los fallos de sesión, backend o pago se presentan sin declarar éxito.

Estos criterios describen objetivos verificables; su aceptación contractual debe registrarse en Jira/acta.
