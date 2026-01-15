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
╔═══════════════════════════════════════════════════════════════════╗
║                     MAX-IDE Agent v1.1.0                          ║
║                                                                   ║
║  Conecta tu Arduino con MAX-IDE desde tu navegador               ║
╚═══════════════════════════════════════════════════════════════════╝


🪟 WINDOWS
──────────
   1. Haz doble clic en: start_agent.bat
   2. ¡Listo! Verás una ventana con "Listening on http://localhost:8765"
   
   Opcional: Ejecuta install_autostart.bat para que inicie con Windows


🍎 macOS
─────────
   1. Abre Terminal (Cmd + Espacio → "Terminal")
   2. Navega a esta carpeta: cd ~/Downloads/maxide-agent
   3. Ejecuta: bash start_agent.sh


🐧 LINUX
─────────
   1. Abre Terminal (Ctrl + Alt + T)
   2. Navega a esta carpeta: cd ~/Descargas/maxide-agent
   3. Ejecuta: bash start_agent.sh
   
   Primera vez? Agrega permisos de puertos serial:
      sudo usermod -a -G dialout $USER
      (Luego cierra sesión y vuelve a entrar)


✅ VERIFICAR QUE FUNCIONA
──────────────────────────
   Abre en tu navegador: http://localhost:8765/health
   
   Si ves {"status": "running"...} → ¡El Agent está listo!


❓ PROBLEMAS COMUNES
─────────────────────
   • "Port busy" / Puerto ocupado
     → Cierra Arduino IDE, Serial Monitor u otras apps que usen el puerto
   
   • "Sync error" / Error de sincronización
     → Prueba otro cable USB o presiona RESET en el Arduino
   
   • Linux no detecta Arduino
     → Ejecuta: sudo usermod -a -G dialout $USER
     → Cierra sesión y vuelve a entrar


📋 REQUISITOS
──────────────
   • Python 3.7 o superior
   • arduino-cli (el instalador lo configura automáticamente)


═══════════════════════════════════════════════════════════════════
                        ¡Disfruta MAX-IDE! 🚀
═══════════════════════════════════════════════════════════════════
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

