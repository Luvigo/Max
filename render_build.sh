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
mkdir -p bin

echo "==> Descargando arduino-cli..."
ARDUINO_CLI_VERSION="1.3.2"
curl -fsSL "https://github.com/arduino/arduino-cli/releases/download/v${ARDUINO_CLI_VERSION}/arduino-cli_${ARDUINO_CLI_VERSION}_Linux_64bit.tar.gz" -o arduino-cli.tar.gz

echo "==> Extrayendo arduino-cli..."
tar -xzf arduino-cli.tar.gz -C bin/
rm arduino-cli.tar.gz

echo "==> Configurando arduino-cli..."
./bin/arduino-cli config init --overwrite || true

echo "==> Instalando core de Arduino AVR..."
./bin/arduino-cli core update-index
./bin/arduino-cli core install arduino:avr

echo "==> Build completado!"
echo "    arduino-cli instalado en: $(pwd)/bin/arduino-cli"
./bin/arduino-cli version

