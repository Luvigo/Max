#!/bin/bash
# =============================================
# Build MAX-IDE Agent distribution package
# =============================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUTPUT_DIR="$SCRIPT_DIR/../editor/static/agent"
PACKAGE_NAME="maxide-agent"

echo "Building MAX-IDE Agent package..."
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Create temp directory for packaging
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="$TEMP_DIR/$PACKAGE_NAME"
mkdir -p "$PACKAGE_DIR"

# Copy agent files
cp "$SCRIPT_DIR/agent.py" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/install.py" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/start_agent.sh" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/start_agent.bat" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/install_autostart.bat" "$PACKAGE_DIR/"

# Make scripts executable
chmod +x "$PACKAGE_DIR/start_agent.sh"
chmod +x "$PACKAGE_DIR/install.py"

# Create README
cat > "$PACKAGE_DIR/LEEME.txt" << 'EOF'
=============================================
MAX-IDE Agent - Guía Rápida
=============================================

El MAX-IDE Agent es un programa que se ejecuta en tu computadora
para permitir subir código a tu Arduino desde MAX-IDE.

INSTALACIÓN RÁPIDA:
-------------------

Windows:
  1. Ejecuta start_agent.bat (doble clic)
  2. (Opcional) Ejecuta install_autostart.bat para inicio automático

Linux/macOS:
  1. Abre terminal en esta carpeta
  2. Ejecuta: bash start_agent.sh
     (El script creará automáticamente un entorno virtual)
  3. (Opcional) Para auto-start: python3 install.py

INSTALACIÓN MANUAL (Linux):
---------------------------
Si prefieres hacerlo manualmente:

  1. Crea entorno virtual:
     python3 -m venv venv-agent
  
  2. Activa el entorno:
     source venv-agent/bin/activate
  
  3. Instala dependencias:
     pip install flask flask-cors pyserial requests
  
  4. Ejecuta el Agent:
     python agent.py --port 8765

REQUISITOS:
-----------
- Python 3.7 o superior
- arduino-cli (se puede instalar con install.py)

VERIFICAR FUNCIONAMIENTO:
------------------------
Abre en tu navegador: http://127.0.0.1:8765/health

Si ves un JSON con "ok": true, ¡el Agent está funcionando!

SOLUCIÓN DE PROBLEMAS:
---------------------
- Si no detecta puertos en Linux, ejecuta:
  sudo usermod -a -G dialout $USER
  (y reinicia sesión)

- Si tienes error "externally-managed-environment":
  El script start_agent.sh crea automáticamente un entorno virtual.
  Si prefieres instalación manual, usa: pip install --user ...

- Si el puerto está ocupado, cierra Arduino IDE u otras apps que lo usen

- Si hay error de sincronización, prueba otro cable USB o presiona RESET

Para más ayuda, visita: https://github.com/tu-repo/max-ide

=============================================
EOF

# Create ZIP
cd "$TEMP_DIR"
zip -r "$OUTPUT_DIR/$PACKAGE_NAME.zip" "$PACKAGE_NAME"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "Package created: $OUTPUT_DIR/$PACKAGE_NAME.zip"
echo ""

# Show contents
echo "Contents:"
unzip -l "$OUTPUT_DIR/$PACKAGE_NAME.zip"

