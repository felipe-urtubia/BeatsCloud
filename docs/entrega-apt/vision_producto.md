# Visión del producto — BeatsCloud

**Corte de implementación:** 19-11-2026. Esta visión describe el producto implementado; no representa validación de mercado ni aprobación comercial.

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
| Sesión Django + CSRF | **Implementado; pruebas funcionales con proveedor externo confirmadas por el equipo** | Código de autenticación; Felipe confirma pruebas funcionales de activación/correo y recuperación/cambio de contraseña. La suite local usa backend de prueba. |
| Catálogo y perfiles | **Implementado; suite automatizada y evidencia local de navegador** | Componentes y APIs presentes; smoke y recorrido visual históricos documentados. |
| Carrito y totales server-side | **Implementado; suite automatizada y evidencia de navegador para carrito** | Contrato API documentado; verificar en el entorno APT actual. |
| Webpay Plus y estados de retorno | **IMPLEMENTADO; suite automatizada con dobles aprobada; Webpay TEST real pendiente** | Vistas, SDK, estados y tests con respuestas sustitutas. Cobro/retorno completo E2E TEST queda **PENDIENTE**. |
| Biblioteca/descarga | **IMPLEMENTADO; pruebas de permisos automatizadas; E2E de compra/descarga pendiente** | Endpoint protegido y cliente SPA presentes; la evidencia solicitada no está adjunta. |
| Carga híbrida de audio | **Implementado; integración local y pruebas automatizadas** | API/cliente conectados; cambios de carga del PR #2 sin ejecución de navegador acreditada en este corte. |
| Modo `mock` | **SIMULADO** | Datos locales de demostración, no valida persistencia, autorización, pago ni descarga real. |
| Audio engine modificado en PR #2 | **Código implementado; la evidencia automatizada no cubre una revisión manual completa del motor de audio** | El código fue actualizado; todavía no se ha comprobado play/pausa, cambio de fuente, volumen ni visualizador en navegador. |
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
- El flujo R2 se encuentra implementado en frontend y backend, pero la operación contra un bucket real, su persistencia y descarga cloud no se acreditan en esta entrega.

## Fuente y alcance

Los roles y capacidades se describen según el código y la documentación académica disponible. No se afirma validación comercial, investigación de mercado ni aceptación por un cliente externo.

## Fuentes

- [Arquitectura](arquitectura.md)
- `app/models.py`, `app/api_shim.py`, `app/views.py`
- `frontend/client/src/context/AppContext.tsx`, `frontend/client/src/api/django.service.ts` y `frontend/client/src/components/ArtistProfilePage.tsx`
- Código vigente: `app/models.py`, `app/api_shim.py`, `app/views.py` y `frontend/client/src/`.
