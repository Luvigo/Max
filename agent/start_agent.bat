@echo off
REM MAX-IDE Agent - Script de inicio (Windows)

cd /d "%~dp0"

REM Verificar Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python no encontrado
    pause
    exit /b 1
)

REM Verificar/crear venv
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
)

REM Activar venv
call venv\Scripts\activate.bat

REM Instalar dependencias
echo Verificando dependencias...
pip install -q -r requirements.txt

REM Ejecutar agent
echo.
python agent.py %*

