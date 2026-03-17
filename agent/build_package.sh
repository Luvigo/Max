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

# Copy README (fuente única: agent/LEEME.txt)
cp "$SCRIPT_DIR/LEEME.txt" "$PACKAGE_DIR/"

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

