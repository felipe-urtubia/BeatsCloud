# Guía de pruebas QA

## Preparar Windows 11

Instala estos programas una sola vez desde sus sitios oficiales. No hace falta elegir opciones avanzadas ni ejecutar el asistente como administrador.

| Programa | Para qué se necesita | Descarga |
|---|---|---|
| Git for Windows | Descargar el proyecto y proporcionar Git Bash | [git-scm.com/download/win](https://git-scm.com/download/win) |
| Python 3.12 o superior | Preparar backend y ejecutar pruebas Django | [python.org/downloads](https://www.python.org/downloads/) |
| Node.js 20 o superior | Preparar y comprobar la página web | [nodejs.org](https://nodejs.org/) |
| Docker Desktop | Ejecutar PostgreSQL de prueba aislado | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |
| FFmpeg | Preparar audio de demostración para catálogo y previews | [ffmpeg.org/download.html](https://ffmpeg.org/download.html) |

Durante la instalación de Python, activa la opción para que Python esté disponible en PATH. Después de instalar programas, cierra y vuelve a abrir la carpeta del proyecto. Abre Docker Desktop y espera a que termine de iniciar. No cambies opciones de seguridad ni compartas tu contraseña.

## Ejecutar

1. Abre la carpeta BeatsCloud que descargaste.
2. Haz doble clic en `INICIAR_QA.bat`.
3. Sigue los mensajes numerados y deja abierta la ventana. La primera corrida instala dependencias y prepara datos; puede tardar más que las siguientes.
4. Al terminar, abre el HTML indicado en `evidencias/qa/runs/`. Conserva también el Markdown equivalente.
5. Si la corrida dice FALLIDO, conserva el informe y el `qa-run.log` privado para pedir ayuda. No envíes la carpeta `.qa-private` completa.

El asistente no instala programas por su cuenta. Si falta algo, muestra su nombre, por qué se usa y dónde obtenerlo. Instálalo, abre Docker Desktop cuando corresponda y vuelve a abrir `INICIAR_QA.bat`.

## Pruebas manuales recomendadas

Los automatismos no sustituyen la revisión del sitio. Anota cada intento en `evidencias/qa/plantillas/PLANTILLA_EVIDENCIA.md`.

1. Abre la página local que informa la ventana de QA y verifica que el catálogo aparezca.
2. Prueba búsqueda, filtros de género y tipo, ordenamiento y paginación. Los datos del catálogo local son semilla sintética.
3. Abre una pista y prueba preview, pausar y reanudar.
4. Inicia sesión con una cuenta QA solo si necesitas revisar funciones autenticadas. Las claves se generan en el equipo; se guardan solo dentro del directorio privado `.qa-private/credenciales-qa.txt` y no se imprimen ni se incluyen en el informe.
5. Prueba carrito y favoritos en cuentas de prueba. No ingreses tarjetas ni datos reales.
6. Registra qué hiciste, qué esperabas y qué ocurrió. Oculta nombres, correos y cualquier información personal en las capturas.

## Lista breve de validación Windows real

El equipo que prepara esta guía no dispone de Windows 11. GitHub Actions ejecuta una comprobación de compatibilidad del launcher en Windows Server, pero no simula Docker ni representa una validación de Windows 11. Vicente debe confirmar en el equipo Windows:

- [ ] Windows 11 detectado y `INICIAR_QA.bat` mantiene la ventana abierta.
- [ ] Ruta de carpeta con espacios en el nombre, por ejemplo `BeatsCloud Pruebas`, funciona.
- [ ] Requisito faltante muestra instrucciones y genera informe FALLIDO sin intentar instalarlo.
- [ ] Docker Desktop detenido se detecta; al abrirlo, el asistente puede ejecutarse otra vez.
- [ ] Corrida completa ejecuta setup, inicio, pruebas, smoke, stop e informes.
- [ ] Una segunda corrida termina sin crear conflictos ni borrar los datos QA anteriores.
- [ ] Interrumpir o provocar una falla ejecuta el intento de detención segura; no detiene contenedores ajenos.
- [ ] El informe HTML y Markdown muestran el mismo SHA y conteos.
- [ ] El log privado no muestra claves ni contraseñas; la carpeta de resultados compartibles no contiene `.env.qa`, bases de datos, medios ni logs privados.

Marca cada casilla solo tras comprobarla. Adjunta captura o nota sin datos sensibles. No conviertas una comprobación estática en resultado aprobado.

## Alcance de las verificaciones automáticas

La corrida comprueba Django, migraciones, pruebas backend y frontend, TypeScript, lint, build y smoke local de Vite/proxy/API, catálogo, preview y rechazo de descarga anónima. No ejecuta una compra real con Webpay, R2 externo, envío SMTP, estudio de usabilidad o carga productiva. Estos límites aparecen también en el informe.
