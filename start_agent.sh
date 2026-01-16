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

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/venv-agent"

# Check if virtual environment exists
if [ -d "$VENV_DIR" ]; then
    echo "✓ Entorno virtual encontrado, activando..."
    source "$VENV_DIR/bin/activate"
    PYTHON="python"  # Use venv python
elif [ -f "$VENV_DIR/bin/activate" ]; then
    echo "✓ Entorno virtual encontrado, activando..."
    source "$VENV_DIR/bin/activate"
    PYTHON="python"  # Use venv python
else
    echo "Creando entorno virtual (recomendado)..."
    $PYTHON -m venv "$VENV_DIR"
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "⚠ No se pudo crear entorno virtual."
        echo "Instalando dependencias con --user (alternativa)..."
        $PYTHON -m pip install flask flask-cors pyserial requests --quiet --user
        
        if [ $? -ne 0 ]; then
            echo "Error instalando dependencias."
            exit 1
        fi
        echo "Dependencias instaladas con --user."
    else
        echo "✓ Entorno virtual creado."
        source "$VENV_DIR/bin/activate"
        PYTHON="python"  # Use venv python
        
        echo "Instalando dependencias en el entorno virtual..."
        pip install flask flask-cors pyserial requests --quiet
        
        if [ $? -ne 0 ]; then
            echo "Error instalando dependencias."
            exit 1
        fi
        echo "✓ Dependencias instaladas."
    fi
fi

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

echo "Iniciando MAX-IDE Agent en http://localhost:8765"
echo ""
echo "Presiona Ctrl+C para detener el Agent."
echo "============================================="
echo ""

# Start agent
$PYTHON "$SCRIPT_DIR/agent.py" --port 8765
