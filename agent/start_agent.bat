@echo off
setlocal
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
if errorlevel 1 goto NO_WINGET
echo       [OK] winget disponible
echo.
goto CHECK_PYTHON

:NO_WINGET
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

REM ========================================
REM PASO 2: Verificar/Instalar Python
REM ========================================
:CHECK_PYTHON
echo [2/5] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 goto INSTALL_PYTHON
echo       [OK] Python encontrado
echo.
goto CHECK_ARDUINO

:INSTALL_PYTHON
echo       Python no encontrado. Instalando con winget...
echo.
echo       Esto puede tardar unos minutos. Por favor espera...
echo.
winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto PYTHON_ERROR
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

:PYTHON_ERROR
echo       ERROR: No se pudo instalar Python.
echo       Intenta instalar Python manualmente desde python.org
pause
exit /b 1

REM ========================================
REM PASO 3: Verificar/Instalar Arduino CLI
REM ========================================
:CHECK_ARDUINO
echo [3/5] Verificando Arduino CLI...
arduino-cli version >nul 2>&1
if errorlevel 1 goto INSTALL_ARDUINO
echo       [OK] Arduino CLI encontrado
echo.
goto CHECK_AVR

:INSTALL_ARDUINO
echo       Arduino CLI no encontrado. Instalando con winget...
echo.
winget install -e --id ArduinoSA.CLI --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto ARDUINO_ERROR
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

:ARDUINO_ERROR
echo       ERROR: No se pudo instalar Arduino CLI.
pause
exit /b 1

REM ========================================
REM PASO 4: Verificar/Instalar Core Arduino AVR
REM ========================================
:CHECK_AVR
echo [4/5] Verificando core arduino:avr...
arduino-cli core list 2>nul | findstr "arduino:avr" >nul
if errorlevel 1 goto INSTALL_AVR
echo       [OK] Core arduino:avr encontrado
echo.
goto CHECK_DEPS

:INSTALL_AVR
echo       Instalando core arduino:avr...
echo       Esto puede tardar unos minutos...
echo.
arduino-cli core update-index
arduino-cli core install arduino:avr
if errorlevel 1 goto AVR_ERROR
echo       [OK] Core arduino:avr instalado
echo.
goto CHECK_DEPS

:AVR_ERROR
echo       ERROR: No se pudo instalar el core arduino:avr.
pause
exit /b 1

REM ========================================
REM PASO 5: Instalar dependencias Python
REM ========================================
:CHECK_DEPS
echo [5/5] Verificando dependencias Python...
python -c "import flask" >nul 2>&1
if errorlevel 1 goto INSTALL_DEPS
echo       [OK] Dependencias ya instaladas
echo.
goto CHECK_AGENT

:INSTALL_DEPS
echo       Instalando dependencias (flask, pyserial, etc.)...
echo.
python -m pip install flask flask-cors pyserial requests
if errorlevel 1 goto DEPS_ERROR
echo       [OK] Dependencias instaladas
echo.
goto CHECK_AGENT

:DEPS_ERROR
echo.
echo       ERROR: No se pudieron instalar las dependencias.
echo       Intenta ejecutar manualmente:
echo       pip install flask flask-cors pyserial requests
echo.
pause
exit /b 1

REM ========================================
REM VERIFICAR QUE AGENT.PY EXISTE
REM ========================================
:CHECK_AGENT
set "SCRIPT_DIR=%~dp0"
set "AGENT_FILE=%SCRIPT_DIR%agent.py"

if exist "%AGENT_FILE%" goto START_AGENT

REM Si no lo encuentra, intentar en el directorio actual
if exist "agent.py" (
    set "AGENT_FILE=agent.py"
    goto START_AGENT
)

echo.
echo ========================================================
echo   ERROR: No se encontro agent.py
echo.
echo   Buscado en: %AGENT_FILE%
echo   Directorio actual: %CD%
echo.
echo   Asegurate de que agent.py esta en la misma
echo   carpeta que start_agent.bat
echo ========================================================
echo.
pause
exit /b 1

REM ========================================
REM INICIAR AGENT
REM ========================================
:START_AGENT
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

python "%AGENT_FILE%" --port 8765

echo.
echo ========================================================
echo   El Agent se ha detenido.
echo ========================================================
echo.
pause
