# Visión del producto — BeatsCloud

**Documento de trabajo; visión de negocio no aprobada por cliente/Product Owner.**
**Corte:** 12-11-2026 · **Presentación APT:** prevista para 19-11-2026

## Visión

BeatsCloud busca ofrecer un espacio digital donde productores presenten sus pistas y artistas descubran instrumentales, escuchen una muestra y, si deciden adquirir una licencia, realicen una compra cuyo resultado y acceso al archivo controla el backend. La experiencia combina catálogo y perfiles musicales con una biblioteca de compras; Django es la autoridad de identidad, transacción y autorización.

Esta declaración resume el propósito implícito en las capacidades del repositorio. La necesidad de mercado, la redacción del cliente y la aprobación de producto deben confirmarse con el equipo.

## Necesidad que busca resolver

La aplicación reúne publicación, descubrimiento y acceso a pistas dentro de un mismo flujo. El código aborda dificultades funcionales observables: localizar productores/tracks, consultar metadatos, mantener una selección y recuperar compras autorizadas. No hay investigación de usuario, entrevistas ni evidencia comercial en los documentos disponibles que permita cuantificar el problema.

## Usuarios objetivo

| Usuario | Necesidad funcional | Respaldo actual |
|---|---|---|
| Productor musical | Presentar perfil y publicar/actualizar tracks con metadatos. | Modelos `Usuario`/`Track`, APIs de perfil/upload y vistas de productor. |
| Artista/comprador | Explorar tracks, gestionar carrito y consultar compras/licencias. | APIs de catálogo, carrito, compras, licencia y componentes de artista. |
| Visitante | Descubrir catálogo y perfiles antes de autenticarse. | APIs públicas de catálogo/usuarios y componentes de exploración. |

El segmento prioritario y personas concretas no están validados; los roles anteriores son roles de dominio presentes en código.

## Propuesta de valor funcional

- Catálogo de tracks y perfiles musicales con metadatos (género/subgénero, BPM, tonalidad, mood y tipo de recurso).
- Vista previa y detalle de pistas; reproducción mediada por el backend.
- Carrito con totales calculados por servidor.
- Pago Webpay Plus con verificación de respuesta en backend antes de registrar la compra.
- Biblioteca e intento de descarga sujeto a autorización de compra.
- Sesiones Django y protección CSRF para operaciones autenticadas.

La ventaja frente a otras plataformas no se ha contrastado; los puntos anteriores describen capacidades, no una afirmación de superioridad comercial.

## Diferenciadores observables y límites de la afirmación

La combinación de perfiles de artista/productor, metadatos de producción y autorización server-side para compras/archivos es una característica del diseño actual. No hay estudio comparativo que permita afirmar que sea única. La reproducción controlada no es DRM. La entrega implementada corresponde al archivo asociado al track, no a stems independientes.

## Estado funcional al corte

| Capacidad | Estado | Base de la clasificación |
|---|---|---|
| Sesión Django + CSRF | **IMPLEMENTADO / VALIDADO históricamente** | Cliente/API y pruebas de autenticación; verificaciones citadas con fecha en `docs/INTEGRACION_BACKEND.md`. No equivale a una prueba completa de entrega actual. |
| Catálogo y perfiles | **IMPLEMENTADO / VALIDADO parcialmente** | Componentes y APIs presentes; smoke y recorrido visual históricos documentados. |
| Carrito y totales server-side | **IMPLEMENTADO / VALIDADO históricamente** | Contrato API documentado; verificar en el entorno APT actual. |
| Webpay Plus y estados de retorno | **IMPLEMENTADO; retorno SIMULADO en algunas pruebas** | Vistas, SDK, estados y tests con respuestas sustitutas. Cobro/retorno completo E2E TEST queda **PENDIENTE**. |
| Biblioteca/descarga | **IMPLEMENTADO; VALIDACIÓN E2E del corte PENDIENTE** | Endpoint protegido y cliente SPA presentes; la evidencia solicitada no está adjunta. |
| Carga híbrida de audio | **IMPLEMENTADO en `main` local; VALIDACIÓN reciente PENDIENTE** | API/cliente conectados; cambios de carga del PR #2 sin ejecución de navegador acreditada en este corte. |
| Modo `mock` | **SIMULADO** | Datos locales de demostración, no valida persistencia, autorización, pago ni descarga real. |
| Audio engine modificado en PR #2 | **PENDIENTE de validación real en navegador** | El código fue actualizado; todavía no se ha comprobado play/pausa, cambio de fuente, volumen ni visualizador en navegador. |
| Operación productiva | **PENDIENTE / no acreditada** | No hay evidencia de despliegue, SLA, monitorización o almacenamiento de producción. |

## Alcance actual y evolución futura

El alcance actual es el que muestran el backend y la SPA: cuentas, roles, catálogo, detalle, interacción social, publicación de pistas, carrito, transacción Webpay y acceso a compras. Prioridades futuras, funcionalidades nuevas, estimaciones y responsables dependen del backlog oficial de Jira, no disponible para esta auditoría. No se presenta ninguna función futura como compromiso.

## Criterios generales de éxito propuestos

Estos criterios son propuestas comprobables y requieren ratificación; no son métricas aprobadas:

1. Un productor autorizado publica un archivo permitido y los metadatos quedan persistidos en Django.
2. Un visitante encuentra y consulta una pista del catálogo con información consistente con la API.
3. Una cuenta autenticada agrega una pista al carrito y ve importes calculados en backend.
4. Una transacción aprobada en Webpay TEST retorna a BeatsCloud y genera una compra verificable; rechazo/cancelación no generan compra.
5. La compra autorizada aparece en la biblioteca y produce una descarga no vacía que se puede abrir/reproducir.
6. La sesión anónima/no autorizada no accede a operaciones privadas ni al archivo completo.
7. Fallos de backend, sesión o pago quedan presentados como error/pendiente, nunca como éxito.

No se fijan umbrales numéricos porque no existen metas aprobadas en las fuentes.

## Limitaciones conocidas

- No se localizó el DOCX E2E ni las capturas requeridas.
- Jira no está conectado en esta sesión; prioridad, compromisos y aceptación de historias no pueden verificarse.
- La integración de pago no debe llamarse “E2E validada” a partir de tests simulados.
- `mock` solo es demostración; debe rotularse como tal.
- El reproductor/audio engine modificado requiere prueba manual de navegador.
- El ZIP `agregar.html` se retiró del árbol actual tras comprobar metadatos: contiene un miembro `.env`, que no se extrajo. El objeto persiste en historial y requiere respuesta de seguridad antes de publicar; este documento no reproduce secretos.

## Pendiente de validación del equipo

El Product Owner/cliente debe confirmar el problema prioritario, la propuesta de valor, segmento objetivo, diferenciadores, métricas/umbrales de éxito, alcance futuro y aceptación de esta visión. Si no existe representante de producto, el equipo debe designar quién tiene autoridad para validar cada punto.

## Fuentes

- [Inicio del proyecto](inicio_proyecto.md)
- [Product Backlog preliminar](product_backlog.md)
- [Arquitectura](arquitectura.md)
- `app/models.py`, `app/api_shim.py`, `app/views.py`
- `frontend/client/src/context/AppContext.tsx`, `frontend/client/src/api/django.service.ts` y `frontend/client/src/components/ArtistProfilePage.tsx`
- [Integración backend](../INTEGRACION_BACKEND.md) y [registro de cambios](../../REGISTRO_CAMBIOS_BEATSCLOUD.md)
