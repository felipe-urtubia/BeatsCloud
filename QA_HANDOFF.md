# Traspaso QA web — Vicente

La validación manual de BeatsCloud se realizará en la aplicación web publicada, desde un navegador. No se requiere clonar el repositorio, instalar herramientas ni ejecutar asistentes locales.

## Aplicación

https://beats-cloud.vercel.app/

## Instrucciones

1. Abrir la URL anterior desde Firefox, Chrome o Edge.
2. Seguir [la guía de primera revisión web](docs/qa/GUIA_VICENTE.md).
3. Ejecutar únicamente los casos de lectura y navegación WEB-01 a WEB-10.
4. Registrar cada resultado y adjuntar capturas cuando exista un problema.
5. Enviar el registro a Ismael para consolidarlo en Jira.

## Restricciones de esta primera ronda

La configuración de Vercel reenvía API, medios, CSRF y sesión al backend `https://beatscloud.onrender.com`. Aún no se ha vinculado el despliegue público a un SHA concreto ni confirmado que la base de datos asociada esté aislada para QA. Por tanto, no registrar cuentas, editar perfiles, cambiar likes/favoritos/carrito, subir/eliminar pistas, comprar, iniciar Webpay ni descargar archivos originales.

Las funciones que requieren autenticación, persistencia o integración externa quedan para una segunda ronda, cuando Felipe confirme backend, base de datos y credenciales de prueba.

## Documentos

- [Guía de Vicente](docs/qa/GUIA_VICENTE.md)
- [Matriz de pruebas basada en Jira](QA_TEST_MATRIX.md)
- [Detalle técnico de las pruebas automatizadas locales](docs/qa/DETALLE_TECNICO.md) — referencia interna; no es el procedimiento que debe ejecutar Vicente.

## Estado

La primera ronda web está preparada, pero todavía no ejecutada. La versión de Vercel debe contrastarse con el SHA de `main` antes de tratar sus resultados como evidencia del corte final.
