#!/bin/bash
# =============================================
# MAX-IDE Agent - Linux/macOS Starter
# =============================================

echo ""
echo "============================================="
echo "      MAX-IDE Agent - Linux/macOS"
echo "============================================="
echo ""

# Detect Python
PYTHON=""
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
fi

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python no encontrado."
    echo ""
    echo "Instala Python 3:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    echo "  macOS: brew install python3"
    echo ""
    exit 1
fi

echo "Python encontrado: $($PYTHON --version)"
echo ""

# Install dependencies
echo "Instalando dependencias..."
$PYTHON -m pip install flask flask-cors pyserial requests --quiet --user

if [ $? -ne 0 ]; then
    echo "Error instalando dependencias."
    exit 1
fi

echo ""
echo "Dependencias instaladas."
echo ""

# Check serial port permissions (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! groups | grep -q dialout; then
        echo "AVISO: Tu usuario no está en el grupo 'dialout'."
        echo "Para acceder a puertos seriales, ejecuta:"
        echo "  sudo usermod -a -G dialout \$USER"
        echo ""
        echo "Luego cierra sesión y vuelve a entrar."
        echo ""
    fi
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Iniciando MAX-IDE Agent en http://localhost:8765"
echo ""
echo "Presiona Ctrl+C para detener el Agent."
echo "============================================="
echo ""

# Start agent
$PYTHON "$SCRIPT_DIR/agent.py" --port 8765
