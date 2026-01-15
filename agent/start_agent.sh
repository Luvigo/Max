#!/bin/bash
# MAX-IDE Agent - Script de inicio

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 no encontrado"
    exit 1
fi

# Verificar/crear venv
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar venv
source venv/bin/activate

# Instalar dependencias
echo "Verificando dependencias..."
pip install -q -r requirements.txt

# Ejecutar agent
echo ""
python3 agent.py "$@"

