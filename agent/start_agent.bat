@echo off
setlocal
title MAX-IDE Agent - Windows
cd /d "%~dp0"

echo.
echo ========================================================
echo            MAX-IDE Agent - Windows
echo ========================================================
echo.
echo   Carpeta actual: %CD%
echo.

REM Verificar si agent.py existe aqui
if not exist "agent.py" (
    echo   ERROR: No se encontro agent.py en esta carpeta.
    echo.
    echo   Si ejecutaste desde dentro del ZIP:
    echo   1. Haz clic derecho en el ZIP
    echo   2. Selecciona "Extraer todo..."
    echo   3. Ejecuta start_agent.bat desde la carpeta extraida
    echo.
    pause
    exit /b 1
)

echo   [OK] agent.py encontrado
echo.
echo   Presiona una tecla para continuar con la instalacion...
pause >nul
echo.

REM ========================================
REM PASO 1: Verificar winget
REM ========================================
echo [1/6] Verificando winget...
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
echo [2/6] Verificando Python...
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
echo [3/6] Verificando Arduino CLI...
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
echo [4/6] Verificando core arduino:avr...
arduino-cli core list 2>nul | findstr "arduino:avr" >nul
if errorlevel 1 goto INSTALL_AVR
echo       [OK] Core arduino:avr encontrado
echo.
goto CHECK_LIBS

:INSTALL_AVR
echo       Instalando core arduino:avr...
echo       Esto puede tardar unos minutos...
echo.
arduino-cli core update-index
arduino-cli core install arduino:avr
if errorlevel 1 goto AVR_ERROR
echo       [OK] Core arduino:avr instalado
echo.
goto CHECK_LIBS

:AVR_ERROR
echo       ERROR: No se pudo instalar el core arduino:avr.
pause
exit /b 1

REM ========================================
REM PASO 5: Verificar/Instalar Librerias Arduino
REM ========================================
:CHECK_LIBS
echo [5/6] Verificando librerias Arduino...
arduino-cli lib list 2>nul | findstr "Servo" >nul
if errorlevel 1 goto INSTALL_LIBS
echo       [OK] Librerias instaladas
echo.
goto CHECK_DEPS

:INSTALL_LIBS
echo       Instalando librerias comunes (Servo, etc.)...
echo.
arduino-cli lib install Servo
if errorlevel 1 goto LIBS_ERROR
echo       [OK] Librerias instaladas
echo.
goto CHECK_DEPS

:LIBS_ERROR
echo       ERROR: No se pudieron instalar las librerias.
echo       Intenta manualmente: arduino-cli lib install Servo
pause
exit /b 1

REM ========================================
REM PASO 6: Instalar dependencias Python
REM ========================================
:CHECK_DEPS
echo [6/6] Verificando dependencias Python...
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
REM LISTO PARA INICIAR
REM ========================================
:CHECK_AGENT
set "AGENT_FILE=agent.py"

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
