@echo off
REM MAAM local - start.bat : SOLO instala todo (se ejecuta UNA vez)
REM No ejecuta el programa. Para correr usa run.bat
setlocal
cd /d "%~dp0"

echo [start] Instalando entorno MAAM local (una sola vez)...

if not exist ".venv\Scripts\python.exe" (
  echo [start] Creando .venv...
  py -m venv .venv
  if errorlevel 1 (
    echo [start] ERROR: no se pudo crear .venv. Instala Python 3.11+ desde python.org
    pause
    exit /b 1
  )
) else (
  echo [start] .venv ya existe, lo reutilizo.
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

echo [start] Creando base de datos...
python local\main_local.py init
if errorlevel 1 (
  echo [start] ERROR creando data.db
  pause
  exit /b 1
)

if not exist "client_secret.json" (
  echo.
  echo [start] AVISO: falta client_secret.json en esta carpeta.
  echo Ponlo aqui y luego usa run.bat para descargar stats.
) else (
  echo [start] client_secret.json OK.
)

echo.
echo [start] LISTO. Ahora usa run.bat para ejecutar el programa.
pause
