# Guía rápida de QA para Vicente

## En una página

1. **Qué descargar:** BeatsCloud desde [GitHub](https://github.com/felipe-urtubia/BeatsCloud), usando la rama `main` que indique el mensaje de entrega. Puedes usar GitHub Desktop: elige **File → Clone repository** y busca `felipe-urtubia/BeatsCloud`.
2. **Qué archivo abrir:** dentro de la carpeta BeatsCloud, haz doble clic en `INICIAR_QA.bat`.
3. **Qué esperar:** se revisarán los programas necesarios, se preparará una base de prueba separada, se ejecutarán verificaciones y aparecerá un resultado. La primera vez puede tardar varios minutos. No cierres la ventana.
4. **Qué enviar cuando termine:** revisa `evidencias/qa/runs/` y envía el `INFORME_VALIDACION.html` o `.md` más reciente. Agrega capturas o notas si hiciste pruebas manuales. La guía está en `docs/qa/GUIA_PRUEBAS.md`.
5. **Qué hacer si aparece un error:** sigue la instrucción que aparece en pantalla. Si no se resuelve, comparte el informe; el `qa-run.log` privado se envía solo a soporte por un canal privado, nunca por GitHub. **No envíes `.env.qa`, `.qa-private` completa ni contraseñas.**

## Windows 11

- Instala Git for Windows, Python 3.12 o superior, Node.js 20 o superior, FFmpeg y Docker Desktop. Los enlaces y motivos están en `docs/qa/GUIA_PRUEBAS.md`.
- Abre Docker Desktop y espera a que indique que está iniciado.
- Desde el Explorador de archivos, entra a la carpeta BeatsCloud y abre `INICIAR_QA.bat` con doble clic.
- Mantén la ventana abierta hasta el mensaje final. No hace falta abrir Docker ni una terminal para los pasos normales.
- Si Windows indica que no es Windows 11 o falta un requisito, instala/abre lo indicado y vuelve a hacer doble clic. El asistente no instala programas ni cambia la seguridad del equipo.

## Linux

- Necesitas Git, Bash, Python 3.12+, Node.js 20+/npm, Docker Compose v2 o Podman Compose rootless, FFmpeg y `curl`.
- Abre la carpeta del repositorio en una terminal y ejecuta `./INICIAR_QA.sh`.
- Conserva abierta esa misma terminal. El asistente prepara, inicia, prueba y detiene todo en esa sesión.

## Evidencias y publicación

Las salidas legibles para compartir quedan en `evidencias/qa/runs/<fecha>/`. Añade capturas, videos y observaciones siguiendo `evidencias/qa/README.md`. Publica los resultados mediante un Pull Request, nunca directamente en `main`; sigue `docs/qa/PUBLICAR_EVIDENCIAS.md`.

## Qué significa el resultado

El informe distingue checks automatizados de verificaciones manuales y servicios externos. Una corrida local no demuestra una compra Webpay real completa, R2 externo con expiración real de enlaces, SMTP real, usabilidad con personas externas ni rendimiento productivo. Si esos casos no se ejecutaron, permanecen como no demostrados.

## Compatibilidad

El flujo Linux puede validarse en Linux. No se dispone de Windows 11 en esta ejecución: la compatibilidad de Windows está revisada estáticamente y requiere completar la lista manual de `docs/qa/GUIA_PRUEBAS.md`. No se declara validación real de Windows hasta que alguien la ejecute allí.
