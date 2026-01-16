#!/bin/bash
# Script para generar certificados SSL autofirmados mejorados para localhost

SSL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SSL_DIR"

echo "Generando certificado SSL para localhost..."

# Obtener la IP local
LOCAL_IP=$(hostname -I | awk '{print $1}')

# Generar clave privada
openssl genrsa -out server.key 2048

# Crear archivo de configuración para el certificado con SAN
cat > server.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = ES
ST = State
L = City
O = MAX-IDE
CN = localhost

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
IP.3 = $LOCAL_IP
EOF

# Generar certificado con SAN (Subject Alternative Name)
openssl req -new -x509 -key server.key -out server.crt -days 365 \
    -config server.conf -extensions v3_req

# Limpiar archivo temporal
rm server.conf

echo "✓ Certificado generado exitosamente"
echo "  - Clave privada: $SSL_DIR/server.key"
echo "  - Certificado: $SSL_DIR/server.crt"
echo "  - Válido para: localhost, 127.0.0.1, ::1, $LOCAL_IP"
echo ""
echo "⚠️  Nota: Este certificado es autofirmado. El navegador mostrará una advertencia."
echo "   Para evitar advertencias, considera usar mkcert: sudo apt install mkcert"
echo ""
echo "Para usar el servidor con SSL, ejecuta:"
echo "  python manage.py runserver_plus --cert-file $SSL_DIR/server.crt --key-file $SSL_DIR/server.key 127.0.0.1:8443"

