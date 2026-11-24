# Matriz de QA funcional web — BeatsCloud

**Corte de backlog:** 24-11-2026  
**Fuente funcional:** Jira, proyecto DDPB.  
**Aplicación de revisión:** https://beats-cloud.vercel.app/  
**Rama de trabajo del producto:** `main`.

## 1. Propósito y regla de ejecución

Esta matriz organiza la primera revisión manual de Vicente según las historias reales del backlog. La revisión se realiza en el navegador, sobre el sitio Vercel ya publicado. No requiere clonar el repositorio ni instalar herramientas.

La primera ronda se limita a navegación y operaciones de lectura. La configuración de `frontend/client/vercel.json` redirige API, medios, CSRF y sesión a `beatscloud.onrender.com`; por lo tanto, una interacción iniciada desde Vercel puede modificar el backend. No hay confirmación registrada aquí de que el despliegue público apunte a una base de datos aislada de QA, y no se ha identificado el SHA desplegado. Hasta confirmarlo, quedan prohibidas las operaciones que escriben datos, generan transacciones o suben/eliminan archivos.

Los casos de esta matriz son **casos por ejecutar**, no resultados. No se asigna APROBADO, FALLIDO ni BLOQUEADO hasta recibir evidencia de Vicente.

## 2. Primera ronda — navegación y lectura segura

| Caso | Procedimiento | Resultado esperado | Historias Jira | Estado |
|---|---|---|---|---|
| WEB-01 Inicio y menú | Abrir la página principal y navegar por el menú. | La página carga y las secciones responden sin errores visibles. | DDPB-20 | Pendiente |
| WEB-02 Géneros y catálogo | Abrir catálogo y secciones de referencia de géneros. | Se visualizan las pistas y sus precios. | DDPB-21, DDPB-24, DDPB-25 | Pendiente |
| WEB-03 Búsqueda | Buscar por nombre de pista y por productor. | Los resultados corresponden al criterio ingresado o se informa que no hay resultados. | DDPB-22, DDPB-26 | Pendiente |
| WEB-04 Datos de pista | Revisar tarjetas y abrir el detalle de una pista disponible. | Nombre, productor, precio, estilo y descripción se muestran de forma coherente. | DDPB-27, DDPB-42, DDPB-43 | Pendiente |
| WEB-05 Filtros y orden | Probar los filtros y órdenes visibles sin añadir ni quitar datos. Registrar criterios y resultados. | La UI responde de forma consistente. El cumplimiento server-side completo se evalúa aparte contra DDPB-70. | DDPB-23, DDPB-28, DDPB-29, DDPB-31, DDPB-70 | Pendiente |
| WEB-06 Preview | Reproducir, pausar y reanudar una muestra; cambiar de pista si está disponible. | Audio y controles mantienen estados coherentes y no se bloquean. | DDPB-30 | Pendiente |
| WEB-07 Perfil artista | Abrir perfiles públicos de artista. | Se distinguen los datos públicos, imágenes, descripción y redes disponibles. | DDPB-14, DDPB-33, DDPB-34, DDPB-35 | Pendiente |
| WEB-08 Perfil productor | Abrir perfiles públicos de productor. | Se visualizan descripción, imágenes, redes y pistas publicadas disponibles. | DDPB-17, DDPB-37, DDPB-38, DDPB-39 | Pendiente |
| WEB-09 Contacto y equipo | Visitar las secciones de contacto y presentación del equipo. | Se muestra la información prevista y los enlaces visibles funcionan. | DDPB-57, DDPB-58 | Pendiente |
| WEB-10 Diseño adaptable | Repetir la navegación con ventana amplia y estrecha. | No hay solapamientos, textos cortados ni controles inaccesibles. | Transversal | Pendiente |

### Registro por caso

Vicente debe completar una fila por caso:

| ID | Resultado (Correcto / Problema / No se pudo comprobar) | Pasos observados | Evidencia | Observación |
|---|---|---|---|---|
| WEB-01 a WEB-10 | Pendiente | — | — | — |

## 3. Segunda ronda — requiere backend de QA confirmado

Estos casos pertenecen al backlog, pero no deben ejecutarse contra un entorno que pueda contener datos reales. Antes se requiere: confirmar SHA desplegado en Vercel, backend asociado en Render, aislamiento de PostgreSQL y credenciales de cuentas sintéticas. Para Webpay se requiere además confirmar explícitamente el ambiente TEST.

| Área / casos | Historias Jira | Qué se debe comprobar | Precondición |
|---|---|---|---|
| Registro y sesión | DDPB-15, DDPB-16, DDPB-18, DDPB-19 | Registro, identificador único, login, cierre de sesión y recuperación. | Cuentas/correos de QA y correo controlado. |
| Perfil editable | DDPB-47, DDPB-48 | Editar y guardar descripción, imagen de perfil y fondo; recargar para verificar persistencia. | Cuenta de QA propia. |
| Likes y favoritos | DDPB-32, DDPB-36 | Agregar/quitar like, persistencia tras recarga y privacidad de favoritos ajenos. | Cuenta de artista y datos de prueba. Las historias siguen pendientes/postergadas en Jira aunque el código está integrado. |
| Carrito | DDPB-54, DDPB-56 | Añadir varias pistas de productores distintos, retirar, revisar subtotal/IVA/total. | Cuenta/ambiente de QA y catálogo de prueba. |
| Checkout y retorno | DDPB-44, DDPB-53, DDPB-55, DDPB-67 | Checkout Webpay TEST, aprobación/rechazo/anulación/abandono, retorno a SPA y habilitación de descarga solo tras aprobación. | Credenciales/ambiente TEST confirmado por Felipe; nunca usar tarjeta real. |
| Historial y licencia | DDPB-46, DDPB-71 | Mostrar solo compras confirmadas del usuario, montos y referencias correctas; consultar licencia verificable desde backend. | Compra de QA autorizada. DDPB-71 sigue pendiente. |
| Descarga y seguridad | DDPB-45, DDPB-73, DDPB-83 | Anónimo y usuario sin compra deben ser rechazados; comprador autorizado accede; enlace vencido deja de funcionar; preview no expone el original. | Compra y archivos de QA; enlaces firmados no deben guardarse ni enviarse. |
| Subida y administración | DDPB-40, DDPB-49, DDPB-50, DDPB-51, DDPB-52, DDPB-72 | Validar precio, metadatos, MP3, flujo directo R2, preview, eliminación lógica/física y conservación de compras previas. | Productor de QA, bucket R2 de prueba y archivos sintéticos. |
| Suscripciones | DDPB-41, DDPB-59, DDPB-60, DDPB-61, DDPB-62, DDPB-63 | Ofertas, precio, condiciones, pago y reporte de incumplimiento. | Historias aún en backlog; no tratar como función aceptada mientras no se implemente. |

## 4. Elementos abiertos del backlog que no deben reportarse como regresión

La revisión debe distinguir error de una funcionalidad que aún no está terminada. Estado actual de Jira consultado el 24-11-2026:

| Ticket | Estado Jira | Tratamiento QA |
|---|---|---|
| DDPB-23 | Tareas por hacer | Registrar el comportamiento visible; no afirmar que el filtro server-side esté cerrado. |
| DDPB-28 | Tareas por hacer | El orden frontend existe; aceptación server-side depende de DDPB-70. |
| DDPB-29 | Tareas por hacer | El orden por género frontend existe; aceptación server-side depende de DDPB-70. |
| DDPB-32 | Tareas por hacer | Código integrado; validar solo en segunda ronda aislada. Etiqueta histórica: postergado. |
| DDPB-36 | Tareas por hacer | Código integrado; validar sólo en segunda ronda aislada. Etiqueta histórica: postergado. |
| DDPB-46 | Tareas por hacer | Historial implementado; falta evidencia de navegador vinculada a compra QA. |
| DDPB-52 | Tareas por hacer | No asumir que retirada/eliminación de pistas está disponible. |
| DDPB-53 / DDPB-55 / DDPB-67 | En curso | Verificar únicamente después de confirmar backend y Webpay TEST. |
| DDPB-59 a DDPB-63 | Tareas por hacer | Suscripciones fuera de la primera ronda; no registrar ausencia como regresión. |
| DDPB-70 | Tareas por hacer | Prioridad High. El contrato server-side para BPM, género, tipo, mood, orden y paginación no está completo según la auditoría de código. Requiere decisión de Felipe. |
| DDPB-71 | Tareas por hacer | Licencia verificable server-side no debe darse por aceptada. |
| DDPB-72 | En curso | Código de carga directa existe; aceptación requiere prueba real de WAV/stems en bucket R2 de QA. |

Además, DDPB-31 figura como finalizada/duplicada respecto del filtro general. DDPB-73 figura finalizada, pero su prueba de expiración sigue siendo una responsabilidad explícita de QA (DDPB-83), no una evidencia que se deba inventar.

## 5. Tareas de QA en Jira

| Ticket | Estado Jira | Alcance |
|---|---|---|
| DDPB-78 | Finalizada | Plan de pruebas y validación de historias revisadas. Esta matriz es la guía de primera ronda web. |
| DDPB-79 | Finalizada | Diseño de escenarios Webpay TEST; la ejecución se registra separadamente. |
| DDPB-82 | Tareas por hacer | Ejecutar pruebas Webpay TEST una vez confirmado entorno seguro. |
| DDPB-83 | En curso | Seguridad de descargas y enlaces expirables; requiere cuentas/archivos de QA. |
| DDPB-84 | Tareas por hacer | Usabilidad con 3–5 participantes; Vicente no debe inventar participantes ni resultados. |
| DDPB-85 | En curso | Integración E2E y regresión, después de habilitar entorno seguro. |
| DDPB-86 | Tareas por hacer | Rendimiento con WAV/stems; requiere R2 de QA y parámetros acordados. |
| DDPB-87 | En curso | Evidencias finales y defensa; registrar resultados reales, no inferirlos. |

## 6. Evidencia técnica existente — no mezclar ejecuciones

Se conservan por separado los resultados automatizados de cada SHA y ambiente. Entre los resultados registrados para el código integrado están 507/507 pruebas Django y 44/44 frontend en el corte de PR #6. La validación Linux del PR #5 corresponde a otro SHA (507 Django / 44 frontend) y el workflow de GitHub ejecutó Windows Server 2025, no Windows 11. PR #5 fue cerrado sin fusionarse; esos resultados no reemplazan la primera revisión web y no se deben atribuir al despliegue Vercel.

El registro de QA del 22-11-2026 documenta una ejecución de integración con Webpay TEST, PostgreSQL, Render, Vercel y R2. Esa evidencia histórica no identifica por sí sola el SHA que está sirviendo el dominio público ahora; tampoco equivale a la nueva ronda manual de Vicente.

## 7. Datos que deben acompañar cualquier resultado

- URL exacta: `https://beats-cloud.vercel.app/`.
- Fecha y hora local.
- Navegador y versión.
- SHA desplegado, solo cuando se confirme en el panel de despliegues de Vercel.
- Backend y ambiente asociados (Render / QA o producción), una vez confirmados.
- ID del caso, pasos, resultado y captura saneada.

**Regla de cierre:** sin evidencia se conserva `Pendiente`; si el entorno no permite una prueba segura se marca `Bloqueado por ambiente`. No cambiar estados Jira ni declarar aceptación únicamente por presencia visual de una pantalla.
