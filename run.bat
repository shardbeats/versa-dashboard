@echo off
REM MAAM local - run.bat : corre la app asumiendo .venv ya existe (rapido, sin instalar)
REM Uso: run.bat [init^|youtube^|beatstars^|stats] [args...]
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [run] No hay .venv. Usa start.bat primero para crear el entorno.
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"

if "%~1"=="" (
  python local\main_local.py stats
) else (
  python local\main_local.py %*
)
