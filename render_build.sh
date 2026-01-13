#!/bin/bash
# Script de build para Render - Instala dependencias y arduino-cli

set -e

echo "==> Instalando dependencias de Python..."
pip install -r requirements.txt

echo "==> Ejecutando migraciones..."
python manage.py migrate

echo "==> Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "==> Creando directorios necesarios..."
mkdir -p sketches

echo "==> Instalando arduino-cli (instalador oficial)..."
# El instalador crea bin/ en el directorio actual
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh

# Mover el binario a bin/ si está en bin/bin/
if [ -f "./bin/bin/arduino-cli" ]; then
    mv ./bin/bin/arduino-cli ./bin/arduino-cli
    rm -rf ./bin/bin 2>/dev/null || true
fi

echo "==> Verificando instalación de arduino-cli..."
./bin/arduino-cli version

echo "==> Configurando arduino-cli..."
./bin/arduino-cli config init --overwrite || true

echo "==> Instalando core de Arduino AVR..."
./bin/arduino-cli core update-index
./bin/arduino-cli core install arduino:avr

echo "==> Build completado!"
echo "    arduino-cli instalado en: $(pwd)/bin/arduino-cli"

