#!/bin/bash
# Script de build para MAX-IDE
# Instala dependencias y configura el proyecto

set -e  # Salir si hay error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              📦 MAX-IDE - Build Script                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado. Por favor instala Python 3.8 o superior."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python encontrado: $(python3 --version)"

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    echo "✓ Entorno virtual creado"
else
    echo "✓ Entorno virtual ya existe"
fi

# Activar entorno virtual
echo ""
echo "🔌 Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo ""
echo "⬆️  Actualizando pip..."
pip install --upgrade pip --quiet

# Instalar dependencias
echo ""
echo "📥 Instalando dependencias..."
pip install -r requirements.txt

echo ""
echo "✓ Dependencias instaladas:"
pip list | grep -E "(django|pyserial|django-extensions|werkzeug|pyOpenSSL)"

# Ejecutar migraciones
echo ""
echo "🗄️  Ejecutando migraciones de base de datos..."
python manage.py migrate --noinput

# Crear directorios necesarios
echo ""
echo "📁 Creando directorios necesarios..."
mkdir -p sketches
mkdir -p ssl
chmod +x ssl/generate_cert.sh 2>/dev/null || true

# Verificar arduino-cli (opcional)
echo ""
if command -v arduino-cli &> /dev/null; then
    echo "✓ arduino-cli encontrado: $(arduino-cli version)"
else
    echo "⚠️  arduino-cli no encontrado (opcional)"
    echo "   Para compilación en servidor, instala:"
    echo "   curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    ✅ Build completado                        ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║                                                               ║"
echo "║  Para iniciar el servidor:                                   ║"
echo "║    ./start_https.sh          (localhost)                      ║"
echo "║    ./start_https_network.sh  (acceso en red)                 ║"
echo "║                                                               ║"
echo "║  Crear superusuario (opcional):                             ║"
echo "║    source venv/bin/activate                                   ║"
echo "║    python manage.py createsuperuser                           ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

