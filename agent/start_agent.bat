@echo off
REM =============================================
REM MAX-IDE Agent - Windows Starter
REM =============================================

echo.
echo =============================================
echo       MAX-IDE Agent - Windows
echo =============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado.
    echo.
    echo Por favor, instala Python desde:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: Marca "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)

echo Python encontrado.
echo.

REM Install dependencies
echo Instalando dependencias...
pip install flask flask-cors pyserial requests --quiet
if errorlevel 1 (
    echo Error instalando dependencias.
    pause
    exit /b 1
)

echo.
echo Dependencias instaladas.
echo.
echo Iniciando MAX-IDE Agent en http://localhost:8765
echo.
echo Presiona Ctrl+C para detener el Agent.
echo =============================================
echo.

REM Start agent
python "%~dp0agent.py" --port 8765

pause
