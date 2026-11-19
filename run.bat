@echo off
REM MAAM local - run.bat : EJECUTA el programa (start.bat ya debio instalarse una vez)
REM Uso: run.bat [init^|youtube^|beatstars^|stats] [...]  o sin args para menu
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [run] No hay .venv. Ejecuta start.bat UNA vez primero para instalar.
  pause
  exit /b 1
)

REM Si hay argumentos, ejecucion directa
if not "%~1"=="" (
  ".venv\Scripts\python.exe" local\main_local.py %*
  echo.
  pause
  exit /b %errorlevel%
)

REM Sin argumentos: menu interactivo
:menu
echo.
echo ===== MAAM local =====
echo 1. Descargar stats de YouTube
echo 2. Importar CSV de BeatStars
echo 3. Ver resumen (stats)
echo 0. Salir
echo.
set "OPT="
set /p OPT="Elige [0-3]: "

if "%OPT%"=="1" (
  ".venv\Scripts\python.exe" local\main_local.py youtube
  echo.
  pause
  goto menu
)
if "%OPT%"=="2" (
  set "CSV="
  set /p CSV="Ruta del CSV de BeatStars: "
  ".venv\Scripts\python.exe" local\main_local.py beatstars --csv "%CSV%"
  echo.
  pause
  goto menu
)
if "%OPT%"=="3" (
  ".venv\Scripts\python.exe" local\main_local.py stats
  echo.
  pause
  goto menu
)
if "%OPT%"=="0" exit /b 0

echo Opcion no valida.
goto menu
