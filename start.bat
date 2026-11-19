@echo off
REM MAAM local - start.bat : crea .venv si falta, instala deps, corre la app
REM Doble-click friendly. Uso: start.bat [init^|youtube^|beatstars^|stats] [args...]
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [start] Creando .venv...
  py -m venv .venv
  if errorlevel 1 (
    echo [start] ERROR: no se pudo crear .venv. Instala Python 3.11+ desde python.org
    pause
    exit /b 1
  )
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul 2>&1
echo [start] Instalando dependencias...
pip install -r local\requirements-local.txt
if errorlevel 1 (
  echo [start] ERROR instalando requirements
  pause
  exit /b 1
)

if "%~1"=="" (
  echo.
  echo Uso: start.bat init ^| youtube ^| beatstars --csv RUTA ^| stats
  echo Ejemplo: start.bat youtube
  echo.
  pause
  exit /b 0
)

python local\main_local.py %*
if errorlevel 1 (
  echo.
  echo [start] Fallo. Revisa client_secret.json / token.json
  pause
  exit /b 1
)
