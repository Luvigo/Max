@echo off
setlocal EnableDelayedExpansion
title MAX-IDE Agent - Windows

echo.
echo ========================================================
echo            MAX-IDE Agent - Windows
echo ========================================================
echo.
echo   Este instalador configurara todo automaticamente
echo.

cd /d "%~dp0"

REM ========================================
REM PASO 1: Verificar winget
REM ========================================
echo [1/5] Verificando winget...
winget --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ========================================================
    echo   ERROR: winget no esta disponible
    echo.
    echo   Soluciones:
    echo   1. Actualiza Windows desde Configuracion
    echo   2. Instala "Instalador de aplicacion" desde
    echo      Microsoft Store
    echo ========================================================
    echo.
    pause
    exit /b 1
)
echo       [OK] winget disponible
echo.

REM ========================================
REM PASO 2: Verificar/Instalar Python
REM ========================================
echo [2/5] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo       Python no encontrado. Instalando con winget...
    echo.
    echo       Esto puede tardar unos minutos. Por favor espera...
    echo.
    winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo       ERROR: No se pudo instalar Python.
        echo       Intenta instalar Python manualmente desde python.org
        pause
        exit /b 1
    )
    echo.
    echo       [OK] Python instalado correctamente
    echo.
    echo ========================================================
    echo   IMPORTANTE: Cierra esta ventana y vuelve a ejecutar
    echo   este archivo para continuar la instalacion.
    echo ========================================================
    echo.
    pause
    exit /b 0
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
    echo       [OK] Python !PYVER! encontrado
)
echo.

REM ========================================
REM PASO 3: Verificar/Instalar Arduino CLI
REM ========================================
echo [3/5] Verificando Arduino CLI...
arduino-cli version >nul 2>&1
if errorlevel 1 (
    echo       Arduino CLI no encontrado. Instalando con winget...
    echo.
    winget install -e --id ArduinoSA.CLI --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo       ERROR: No se pudo instalar Arduino CLI.
        pause
        exit /b 1
    )
    echo.
    echo       [OK] Arduino CLI instalado correctamente
    echo.
    echo ========================================================
    echo   IMPORTANTE: Cierra esta ventana y vuelve a ejecutar
    echo   este archivo para continuar la instalacion.
    echo ========================================================
    echo.
    pause
    exit /b 0
) else (
    echo       [OK] Arduino CLI encontrado
)
echo.

REM ========================================
REM PASO 4: Verificar/Instalar Core Arduino AVR
REM ========================================
echo [4/5] Verificando core arduino:avr...
arduino-cli core list 2>nul | findstr /C:"arduino:avr" >nul
if errorlevel 1 (
    echo       Instalando core arduino:avr...
    echo       Esto puede tardar unos minutos (descarga ~100MB)...
    echo.
    arduino-cli core update-index
    arduino-cli core install arduino:avr
    if errorlevel 1 (
        echo       ERROR: No se pudo instalar el core arduino:avr.
        pause
        exit /b 1
    )
    echo       [OK] Core arduino:avr instalado
) else (
    echo       [OK] Core arduino:avr encontrado
)
echo.

REM ========================================
REM PASO 5: Instalar dependencias Python
REM ========================================
echo [5/5] Verificando dependencias Python...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo       Instalando dependencias (flask, pyserial, etc.)...
    pip install flask flask-cors pyserial requests --quiet --disable-pip-version-check
    if errorlevel 1 (
        echo       ERROR: No se pudieron instalar las dependencias.
        pause
        exit /b 1
    )
    echo       [OK] Dependencias instaladas
) else (
    echo       [OK] Dependencias ya instaladas
)
echo.

REM ========================================
REM INICIAR AGENT
REM ========================================
echo.
echo ========================================================
echo.
echo   [OK] Todo listo! Iniciando MAX-IDE Agent...
echo.
echo   - Abre MAX-IDE en tu navegador
echo   - NO cierres esta ventana mientras programas
echo.
echo ========================================================
echo.
echo   Agent corriendo en: http://localhost:8765
echo.
echo   Presiona Ctrl+C para detener el Agent.
echo --------------------------------------------------------
echo.

python "%~dp0agent.py" --port 8765

echo.
echo ========================================================
echo   El Agent se ha detenido.
echo ========================================================
pause
