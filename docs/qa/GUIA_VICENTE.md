# Primera revisión web de BeatsCloud — Vicente

**Fecha de preparación:** 24-11-2026  
**Aplicación:** https://beats-cloud.vercel.app/  
**Tipo de revisión:** funcional manual desde navegador, contra el sitio publicado.

## 1. Qué tienes que hacer

1. Abre https://beats-cloud.vercel.app/ en Firefox, Chrome o Edge.
2. No descargues el proyecto, no instales programas y no ejecutes archivos del repositorio.
3. Recorre los casos de la sección 3 y revisa si la aplicación se comporta como se describe.
4. Anota el resultado de cada caso: **Correcto**, **Problema** o **No se pudo comprobar**.
5. Cuando encuentres un problema, guarda una captura y anota qué hiciste justo antes de que apareciera.

Esta es una primera revisión del producto web. No es necesario configurar Windows, Python, Node, Docker ni FFmpeg.

## 2. Límite importante de esta primera ronda

La configuración versionada de Vercel reenvía las rutas `/api`, `/media`, `/csrf/` y `/session/` a `https://beatscloud.onrender.com`. Por eso, probar la URL de Vercel también puede interactuar con el backend y sus datos.

Aún no se ha podido confirmar desde esta revisión que el despliegue público use una base de datos aislada para QA ni vincular la versión publicada a un SHA concreto de `main`.

**Por seguridad, en esta primera ronda haz solo pruebas de lectura y navegación. No realices estas acciones:**

- No envíes formularios de registro ni recuperación de contraseña.
- No edites perfiles, publiques o elimines pistas, ni cambies información.
- No agregues o quites likes/favoritos ni modifiques el carrito.
- No inicies pagos, no uses Webpay y no ingreses datos personales o bancarios.
- No descargues archivos originales ni compartas enlaces de descarga.
- No subas archivos de audio.

Si una prueba te pide alguna de esas acciones, sáltala y marca **No se pudo comprobar — requiere entorno de QA**. No intentes improvisar datos.

## 3. Casos de revisión de esta primera ronda

| ID | Qué revisar | Historias Jira relacionadas | Resultado esperado |
|---|---|---|---|
| WEB-01 | Abrir la página principal y recorrer el menú. | DDPB-20 | Las secciones abren correctamente y el menú permite ubicarse. |
| WEB-02 | Revisar las referencias de géneros y el catálogo. | DDPB-21, DDPB-24, DDPB-25 | El catálogo carga y las pistas visibles muestran su información y precio sin errores evidentes. |
| WEB-03 | Buscar una pista y un productor desde los buscadores disponibles. | DDPB-22, DDPB-26 | La búsqueda responde y los resultados coinciden razonablemente con el texto ingresado. |
| WEB-04 | Revisar tarjetas y detalle de pistas. | DDPB-27, DDPB-42, DDPB-43 | Se ve el nombre, productor, precio, estilo y descripción cuando corresponda; no hay datos rotos o vacíos inesperados. |
| WEB-05 | Probar los filtros y las opciones de orden visibles, sin modificar datos. | DDPB-23, DDPB-28, DDPB-29, DDPB-31, DDPB-70 | Anota qué filtros y órdenes funcionan y qué resultados muestran. El filtrado completo server-side de DDPB-70 sigue pendiente en Jira: no lo marques como aprobado por observar un filtro visual. |
| WEB-06 | Reproducir un preview, pausarlo y reanudarlo; probar cambiar de pista si la interfaz lo permite. | DDPB-30 | El audio comienza, se pausa y continúa sin quedarse bloqueado; los controles y el tiempo se comportan de forma coherente. |
| WEB-07 | Abrir perfiles públicos de artista. | DDPB-14, DDPB-33, DDPB-34, DDPB-35 | Se identifica el perfil de artista y se muestran los datos públicos disponibles. |
| WEB-08 | Abrir perfiles públicos de productor. | DDPB-17, DDPB-37, DDPB-38, DDPB-39 | Se identifica el productor y se muestran descripción, imágenes y redes disponibles. |
| WEB-09 | Revisar las secciones de contacto y equipo. | DDPB-57, DDPB-58 | Se muestran los datos y la información de equipo que corresponden. |
| WEB-10 | Recorrer la aplicación en una ventana de escritorio y otra más estrecha. | Transversal | Textos, controles y tarjetas siguen siendo utilizables; no hay elementos superpuestos ni secciones inaccesibles. |

## 4. Funciones que se validarán en una segunda ronda

Estas historias siguen dentro del backlog, pero necesitan cuentas de prueba y confirmación del entorno antes de modificar datos:

- **Cuenta y sesión:** DDPB-15, DDPB-16, DDPB-18 y DDPB-19.
- **Perfil y datos del usuario:** DDPB-47 y DDPB-48.
- **Likes y lista de interesados:** DDPB-32 y DDPB-36. La implementación está integrada en `main`, pero Jira aún las muestra como pendientes/postergadas.
- **Carrito, pago, historial y descarga:** DDPB-44, DDPB-45, DDPB-46, DDPB-53, DDPB-54, DDPB-55, DDPB-56, DDPB-67, DDPB-71 y DDPB-73.
- **Publicación y administración de pistas:** DDPB-40, DDPB-49, DDPB-50, DDPB-51, DDPB-52 y DDPB-72.
- **Suscripciones:** DDPB-41 y DDPB-59 a DDPB-63.

No todas esas historias están finalizadas en Jira. Las que estén en `En curso` o `Tareas por hacer` no deben marcarse como aprobadas solo porque una parte de su interfaz exista.

## 5. Qué enviar al terminar

Comparte un resumen breve con:

- Navegador y versión, si la conoces.
- Fecha y hora aproximada de la revisión.
- Resultado de WEB-01 a WEB-10.
- Capturas de los problemas encontrados.
- Una frase indicando qué acción estabas realizando cuando apareció cada problema.

No incluyas contraseñas, cookies, tokens, datos personales, datos bancarios ni enlaces firmados. No es necesario cambiar estados de Jira; Ismael consolidará los resultados.

Gracias por revisar la aplicación. Si algún paso no está disponible, indícalo tal como aparece en pantalla; no intentes corregirlo ni rodearlo.
