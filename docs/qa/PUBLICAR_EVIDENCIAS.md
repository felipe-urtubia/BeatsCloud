# Publicar evidencias QA con un Pull Request

Los informes se pueden compartir después de revisar que contienen el SHA correcto y no tienen datos privados. **No publiques directamente en `main`.**

## Antes de publicar

1. Abre `evidencias/qa/runs/` y revisa el informe más reciente.
2. Añade capturas a `evidencias/qa/screenshots/`, videos a `evidencias/qa/videos/` y observaciones a `evidencias/qa/execution-notes/`.
3. Quita rostros, nombres, correos, identificadores de usuario, cookies, cabeceras de autorización, tokens, números de tarjeta y URLs firmadas.
4. No añadas `.env`, `.env.qa`, `.qa-private/`, `media/`, `.venv/`, `node_modules/`, archivos de base de datos ni logs privados. Si soporte pide el log, entrégalo solo por un canal privado fuera de GitHub.
5. Asegúrate de que el PR incluya un resumen y enlace o ruta del `INFORME_VALIDACION.html`.

## Opción A: GitHub Desktop (recomendada)

1. Instala y abre [GitHub Desktop](https://desktop.github.com/), inicia sesión con tu cuenta GitHub y agrega la carpeta BeatsCloud si no aparece.
2. En la barra superior elige la rama `main`; selecciona **Fetch origin** y luego **Pull origin** si GitHub Desktop lo ofrece.
3. Elige **Branch → New branch**, escribe `qa/evidencias-vicente-AAAA-MM-DD` y créala desde `main`.
4. En los cambios, selecciona solo el informe de `evidencias/qa/runs/<fecha>/` y las capturas/notas que revisaste. No selecciones archivos privados.
5. Escribe un resumen con resultado APROBADO/FALLIDO, SHA, sistema operativo, pruebas manuales realizadas y límites no probados. Haz clic en **Commit to ...**.
6. Haz clic en **Publish branch** y después en **Create Pull Request**. En GitHub, revisa el título, la base (`main`), los archivos y el informe enlazado antes de crear el PR.
7. Espera revisión. No uses botones de merge.

## Opción B: GitHub CLI

Abre Git Bash dentro del repositorio. Si todavía no iniciaste sesión, ejecuta `gh auth login` y sigue las instrucciones oficiales. Después ejecuta, cambiando la fecha y el directorio de informe por los tuyos:

```bash
git switch main
git pull --ff-only origin main
git switch -c qa/evidencias-vicente-AAAA-MM-DD
git status --short
git add evidencias/qa/runs/FECHA/INFORME_VALIDACION.md evidencias/qa/runs/FECHA/INFORME_VALIDACION.html evidencias/qa/screenshots evidencias/qa/videos evidencias/qa/execution-notes
git diff --cached --check
git diff --cached --name-only
```

Revisa la lista y el contenido preparado. Si hay `.env.qa`, `.qa-private`, credenciales, base de datos, medios, cookies o datos de pago, no continúes: quítalos del área preparada con GitHub Desktop o `git restore --staged RUTA`.

Cuando solo estén los archivos revisados:

```bash
git commit -m "docs(qa): agrega resultados de Vicente"
git push -u origin qa/evidencias-vicente-AAAA-MM-DD
gh pr create --base main --head qa/evidencias-vicente-AAAA-MM-DD --title "Evidencias QA de Vicente" --body "Resultado: APROBADO/FALLIDO. SHA probado: SHA_COMPLETO. Sistema: Windows 11. Informe: evidencias/qa/runs/FECHA/INFORME_VALIDACION.html. Pruebas manuales: resumen. Límites no probados: Webpay real, R2 externo, SMTP real, usabilidad externa y carga productiva."
```

Después abre el PR en GitHub y confirma que `main` sea la base. No hagas merge.

## Si GitHub CLI no tiene sesión

Ejecuta `gh auth login` y selecciona GitHub.com, HTTPS y autenticación con navegador. Si prefieres no usar la terminal, usa GitHub Desktop e inicia sesión allí. No pegues tokens en mensajes, informes ni archivos del repositorio.

## Plantilla del resumen del Pull Request

```text
Resultado: APROBADO / FALLIDO
SHA probado:
Sistema operativo:
Informe: ruta evidencias/qa/runs/<fecha>/INFORME_VALIDACION.html
Pruebas manuales realizadas:
Errores o limitaciones:
No probado: Webpay E2E real, R2 externo, SMTP real, usabilidad externa y carga productiva.
Confirmo que revisé los archivos y no añadí credenciales ni datos personales.
```
