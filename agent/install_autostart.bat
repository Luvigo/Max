@echo off
REM =============================================
REM MAX-IDE Agent - Windows Auto-start Installer
REM =============================================

echo.
echo =============================================
echo  MAX-IDE Agent - Configurar Inicio Automatico
echo =============================================
echo.

REM Create startup shortcut
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set AGENT_DIR=%~dp0
set VBS_FILE=%AGENT_DIR%start_silent.vbs

REM Create VBS for silent startup
echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_FILE%"
echo WshShell.CurrentDirectory = "%AGENT_DIR%" >> "%VBS_FILE%"
echo WshShell.Run "pythonw ""%AGENT_DIR%agent.py"" --port 8765", 0, False >> "%VBS_FILE%"

REM Create BAT in Startup folder
echo @echo off > "%STARTUP_DIR%\MAX-IDE-Agent.bat"
echo wscript.exe "%VBS_FILE%" >> "%STARTUP_DIR%\MAX-IDE-Agent.bat"

echo.
echo MAX-IDE Agent se configuró para iniciar automáticamente con Windows.
echo.
echo Para desinstalar, elimina:
echo   %STARTUP_DIR%\MAX-IDE-Agent.bat
echo.
echo Iniciando Agent ahora...
echo.

REM Start agent now
start "" wscript.exe "%VBS_FILE%"

echo Agent iniciado en segundo plano.
echo Verifica en: http://localhost:8765/health
echo.
pause

