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
cp "$SCRIPT_DIR/boards_registry.json" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/install.py" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$PACKAGE_DIR/"
# Normalizar start_agent.sh a LF (evitar CRLF que rompe en Linux/macOS)
sed 's/\r$//' "$SCRIPT_DIR/start_agent.sh" > "$PACKAGE_DIR/start_agent.sh"
cp "$SCRIPT_DIR/start_agent.bat" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/install_autostart.bat" "$PACKAGE_DIR/"

# Make scripts executable
chmod +x "$PACKAGE_DIR/start_agent.sh"
chmod +x "$PACKAGE_DIR/install.py"

# Sincronizar board registry al static del IDE (fuente única: agent/boards_registry.json)
STATIC_JSON_DIR="$SCRIPT_DIR/../editor/static/editor/json"
mkdir -p "$STATIC_JSON_DIR"
cp "$SCRIPT_DIR/boards_registry.json" "$STATIC_JSON_DIR/boards.json"
echo "  + boards_registry.json → editor/static/editor/json/boards.json"

# Create README
cat > "$PACKAGE_DIR/LEEME.txt" << 'EOF'
╔═══════════════════════════════════════════════════════════════════╗
║                     MAX-IDE Agent v1.1.0                          ║
║                                                                   ║
║  Conecta tu Arduino con MAX-IDE desde tu navegador               ║
╚═══════════════════════════════════════════════════════════════════╝


🪟 WINDOWS
──────────
   1. Descarga Python de https://python.org (marca "Add to PATH")
   
   2. Abre CMD o PowerShell y ejecuta:
      winget install -e --id ArduinoSA.CLI
      arduino-cli core update-index
      arduino-cli core install arduino:avr
   
   3. Haz doble clic en: start_agent.bat
   
   Opcional: Ejecuta install_autostart.bat para inicio automático


🍎 macOS
─────────
   1. Instala arduino-cli:
      brew install arduino-cli
      arduino-cli core install arduino:avr
   
   2. Ejecuta el Agent:
      cd ~/Downloads/maxide-agent
      bash start_agent.sh


🐧 LINUX (Ubuntu/Debian/etc)
─────────────────────────────
   ⚠️  NO uses "snap install arduino-cli" - tiene problemas de permisos.
   
   1. Instala arduino-cli (versión oficial):
      curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
      sudo mv bin/arduino-cli /usr/local/bin/
      arduino-cli core update-index
      arduino-cli core install arduino:avr
   
   2. Agrega permisos de puerto serial:
      sudo usermod -a -G dialout $USER
      (Cierra sesión y vuelve a entrar)
   
   3. Ejecuta el Agent:
      cd ~/Descargas/maxide-agent
      bash start_agent.sh


✅ VERIFICAR QUE FUNCIONA
──────────────────────────
   Abre en tu navegador: http://localhost:8765/health
   
   Si ves {"status": "running"...} → ¡El Agent está listo!


❓ PROBLEMAS COMUNES
─────────────────────
   • "command not found" o "syntax error" al ejecutar start_agent.sh (Mac/Linux)
     → En la carpeta maxide-agent ejecuta (luego: bash start_agent.sh):
       Mac:  sed -i '' 's/\r$//' start_agent.sh
             sed -i '' 's/&> \/dev\/null/> \/dev\/null 2>\&1/g' start_agent.sh
       Linux: sed -i.bak 's/\r$//' start_agent.sh
             sed -i.bak 's/&> \/dev\/null/> \/dev\/null 2>\&1/g' start_agent.sh
   
   • "Permission denied" en Linux
     → NO uses snap. Desinstala con: sudo snap remove arduino-cli
     → Instala la versión binaria oficial (ver arriba)
   
   • "Port busy" / Puerto ocupado
     → Cierra Arduino IDE, Serial Monitor u otras apps
   
   • "Sync error" / Error de sincronización
     → Prueba otro cable USB o presiona RESET en el Arduino


📋 REQUISITOS
──────────────
   • Python 3.7 o superior
   • arduino-cli (versión binaria oficial, NO snap)


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

