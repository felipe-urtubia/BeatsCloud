@echo off
setlocal
cd /d "%~dp0"

echo BEATSCLOUD - VALIDACION QA
echo Revisando Windows y preparando el asistente...

set "WINDOWS_INFO="
for /f "usebackq delims=" %%B in (`powershell.exe -NoProfile -Command "$os=Get-CimInstance Win32_OperatingSystem; '{0}:{1}' -f $os.BuildNumber,$os.ProductType" 2^>nul`) do set "WINDOWS_INFO=%%B"
if not defined WINDOWS_INFO (
  echo No pude comprobar la version de Windows.
  echo Abre Windows PowerShell y verifica que este equipo use Windows 11.
  echo Despues vuelve a abrir INICIAR_QA.bat.
  echo.
  pause
  exit /b 2
)
for /f "tokens=1,2 delims=:" %%A in ("%WINDOWS_INFO%") do (
  set "WINDOWS_BUILD=%%A"
  set "WINDOWS_PRODUCT_TYPE=%%B"
)
if not "%WINDOWS_PRODUCT_TYPE%"=="1" (
  echo Este asistente requiere Windows 11 de escritorio; Windows Server no es compatible.
  echo Usa un equipo Windows 11 y vuelve a abrir este archivo.
  echo.
  pause
  exit /b 2
)
if %WINDOWS_BUILD% LSS 22000 (
  echo Este asistente requiere Windows 11. Tu version de Windows no cumple el requisito.
  echo Consulta Configuracion ^> Sistema ^> Acerca de para revisar la version.
  echo.
  pause
  exit /b 2
)

set "QA_BASH="
where bash.exe >nul 2>nul
if not errorlevel 1 set "QA_BASH=bash.exe"
if not defined QA_BASH if exist "%ProgramFiles%\Git\bin\bash.exe" set "QA_BASH=%ProgramFiles%\Git\bin\bash.exe"
if not defined QA_BASH if exist "%ProgramFiles(x86)%\Git\bin\bash.exe" set "QA_BASH=%ProgramFiles(x86)%\Git\bin\bash.exe"
if not defined QA_BASH (
  echo No encuentro Git Bash. Se instala junto con Git for Windows.
  echo Instala Git desde https://git-scm.com/download/win y vuelve a abrir este archivo.
  echo.
  pause
  exit /b 2
)

"%QA_BASH%" "%~dp0scripts\qa\run-all.sh"
set "QA_RESULT=%ERRORLEVEL%"
echo.
if "%QA_RESULT%"=="0" (echo Resultado correcto. Revisa el informe y las evidencias.) else (echo La validacion fallo. Lee el informe y la siguiente accion indicada.)
echo No compartas .env.qa ni la carpeta .qa-private.
echo.
pause
exit /b %QA_RESULT%
