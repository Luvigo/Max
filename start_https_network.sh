#!/bin/bash
# Script para iniciar el servidor Django con HTTPS accesible desde la red
# Web Serial API requiere HTTPS para funcionar desde otros PCs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Obtener IP local
LOCAL_IP=$(hostname -I | awk '{print $1}')

SSL_DIR="$SCRIPT_DIR/ssl"
mkdir -p "$SSL_DIR"

# Verificar si mkcert está instalado
if command -v mkcert &> /dev/null; then
    CERT_FILE="$SSL_DIR/network.pem"
    KEY_FILE="$SSL_DIR/network-key.pem"
    
    # Regenerar certificados si la IP cambió o no existen
    if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
        echo "🔐 Generando certificados SSL con mkcert..."
        cd "$SSL_DIR"
        mkcert -install 2>/dev/null
        mkcert -cert-file network.pem -key-file network-key.pem \
            localhost 127.0.0.1 ::1 "$LOCAL_IP" "*.local"
        cd "$SCRIPT_DIR"
        echo "✓ Certificados generados"
    fi
else
    # Usar OpenSSL si mkcert no está disponible
    CERT_FILE="$SSL_DIR/network.crt"
    KEY_FILE="$SSL_DIR/network.key"
    
    if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
        echo "🔐 Generando certificados SSL autofirmados..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$KEY_FILE" \
            -out "$CERT_FILE" \
            -subj "/CN=MAX-IDE" \
            -addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:$LOCAL_IP"
        echo "✓ Certificados generados (autofirmados)"
    fi
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           🚀 MAX-IDE - Servidor HTTPS para Red               ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║                                                               ║"
echo "║  📍 URL Local:    https://localhost:8443                      ║"
echo "║  📍 URL Red:      https://$LOCAL_IP:8443                    ║"
echo "║                                                               ║"
echo "║  ⚡ Web Serial API habilitado para clientes en red           ║"
echo "║                                                               ║"
echo "║  ⚠️  En los clientes:                                         ║"
echo "║     1. Abrir https://$LOCAL_IP:8443                         ║"
echo "║     2. Aceptar el certificado SSL                            ║"
echo "║     3. Usar Chrome, Edge u Opera                             ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Iniciar servidor con SSL en todas las interfaces
python manage.py runserver_plus \
    --cert-file "$CERT_FILE" \
    --key-file "$KEY_FILE" \
    0.0.0.0:8443

