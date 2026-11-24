@echo off
setlocal
cd /d "%~dp0"
set "QA_BASH="
where bash.exe >nul 2>nul
if not errorlevel 1 set "QA_BASH=bash.exe"
if not defined QA_BASH if exist "%ProgramFiles%\Git\bin\bash.exe" set "QA_BASH=%ProgramFiles%\Git\bin\bash.exe"
if not defined QA_BASH if exist "%ProgramFiles(x86)%\Git\bin\bash.exe" set "QA_BASH=%ProgramFiles(x86)%\Git\bin\bash.exe"
if not defined QA_BASH (
  echo No encuentro Git Bash.
  echo Instala Git for Windows desde https://git-scm.com/download/win y vuelve a abrir INICIAR_QA.bat.
  echo.
  pause
  exit /b 2
)
"%QA_BASH%" "%~dp0scripts\qa\run-all.sh"
set "QA_RESULT=%ERRORLEVEL%"
echo.
if "%QA_RESULT%"=="0" (echo Resultado correcto.) else (echo La validacion fallo. Sigue las instrucciones del informe.)
pause
exit /b %QA_RESULT%
