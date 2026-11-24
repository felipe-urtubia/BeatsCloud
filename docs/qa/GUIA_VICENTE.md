# Guía rápida para Vicente

## Lo esencial

1. **Qué descargar:** el proyecto BeatsCloud desde su repositorio y la rama `main` indicada en el mensaje de entrega. No necesitas descargar ni aplicar un parche aparte.
2. **Qué abrir:** en Windows, `INICIAR_QA.bat`; en Linux, abre una terminal en la carpeta del proyecto y ejecuta `./INICIAR_QA.sh`.
3. **Qué esperar:** el asistente revisará los programas necesarios, preparará datos de prueba, ejecutará la validación y detendrá los servicios. Puede tardar mientras instala dependencias la primera vez. No cierres la ventana.
4. **Qué enviar:** al final, envía `INFORME_VALIDACION.md`. Si el resultado dice FALLIDO, envía también `qa-run.log` desde la ruta privada que muestra el asistente.
5. **Si aparece un error:** deja la ventana abierta, lee el mensaje y sigue la instrucción indicada. Si no se resuelve, envía el informe y `qa-run.log`. **Nunca envíes `.env.qa`**.

## Windows 10/11

Necesitas Git for Windows (incluye Git Bash), Python 3.12 o superior, Node.js LTS, FFmpeg y Docker Desktop con Compose. Instálalos desde sus sitios oficiales y abre Docker Desktop antes de comenzar. El asistente no instala programas ni pide permisos de administrador.

1. Descarga o clona el repositorio y cambia a la versión indicada en la entrega.
2. Abre la carpeta del proyecto y haz doble clic en `INICIAR_QA.bat`.
3. Si Windows pregunta si permites ejecutar el archivo, comprueba que provenga del paquete oficial que recibiste. No desactives antivirus ni controles de seguridad.
4. La ventana permanece abierta al final. Sigue el mensaje final para localizar el informe.

**Estado de compatibilidad:** el lanzador y las rutas Windows se revisaron estáticamente. Esta versión no se ejecutó en Windows, por lo que Windows 10/11 aún requiere una corrida real antes de declarar compatibilidad comprobada.

## Linux

Necesitas Git, Bash, Python 3.12 o superior, Node.js 20 o superior con npm, Docker Compose v2 (o Podman Compose rootless) y FFmpeg. Docker/Podman debe estar iniciado y tu usuario debe tener acceso sin elevar privilegios desde el asistente.

1. Abre una terminal dentro de la carpeta del proyecto.
2. Ejecuta `./INICIAR_QA.sh`.
3. Mantén esa terminal abierta hasta que aparezca el resultado final.

`setup.sh`, `start.sh`, `verify.sh` y `stop.sh` se ejecutan secuencialmente desde una misma sesión persistente. No abras otra terminal para continuar el flujo.

## Datos y privacidad

El asistente crea credenciales locales nuevas cuando prepara por primera vez las cuentas QA. Los archivos privados y los logs se guardan en `.qa-private/`; no compartas `.env.qa`. La base y los medios de QA se conservan después de la ejecución para que no se pierdan los datos. El asistente no borra datos automáticamente.

No se incluyen capturas de pantalla: no se realizó una sesión gráfica reproducible para capturarlas.
