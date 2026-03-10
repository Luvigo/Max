#!/bin/bash
# Script para iniciar el servidor Django con HTTPS

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Verificar que existan los certificados
SSL_DIR="$SCRIPT_DIR/ssl"

# Intentar usar certificados de mkcert primero (más confiables)
CERT_FILE="$SSL_DIR/localhost+2.pem"
KEY_FILE="$SSL_DIR/localhost+2-key.pem"

# Si no existen certificados de mkcert, usar los autofirmados
if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    CERT_FILE="$SSL_DIR/server.crt"
    KEY_FILE="$SSL_DIR/server.key"
    
    if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
        echo "⚠️  Certificados SSL no encontrados. Generando..."
        "$SSL_DIR/generate_cert.sh"
    fi
fi

echo "🚀 Iniciando servidor Django con HTTPS..."
echo "📍 URL local: https://localhost:8443"
echo ""

# Verificar si estamos usando certificados de mkcert
if [[ "$CERT_FILE" == *"localhost+2.pem"* ]]; then
    echo "✓ Usando certificados de mkcert (sin advertencias)"
else
    echo "⚠️  Usando certificados autofirmados"
    echo "   El navegador mostrará una advertencia de seguridad."
    echo "   Para evitar advertencias, instala mkcert: sudo apt install mkcert"
    echo "   Luego ejecuta: cd ssl && mkcert localhost 127.0.0.1 ::1"
    echo ""
fi

# Iniciar servidor con SSL (solo localhost para desarrollo)
python manage.py runserver_plus \
    --cert-file "$CERT_FILE" \
    --key-file "$KEY_FILE" \
    127.0.0.1:8443

