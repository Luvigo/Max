#!/bin/bash
# Script de build para Render - Instala dependencias y arduino-cli

set -e

# Directorio base del proyecto
PROJECT_DIR=$(pwd)

echo "==> Instalando dependencias de Python..."
pip install -r requirements.txt

echo "==> Ejecutando migraciones..."
python manage.py migrate

# ⚠️ DESACTIVADO: Los datos de prueba se recreaban en cada deploy
# Si necesitas crear datos de prueba, ejecuta manualmente:
# python manage.py create_test_data
# echo "==> Creando datos de prueba (usuarios, cursos, etc.)..."
# python manage.py create_test_data || echo "Datos de prueba ya existen o error al crear"

echo "==> Verificando/creando usuario admin..."
python manage.py create_admin --username admin --email admin@maxide.com --password admin123 || echo "Usuario admin ya existe"

echo "==> Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "==> Creando directorios necesarios..."
mkdir -p sketches
mkdir -p arduino-data
mkdir -p arduino-data/staging

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

# Configurar arduino-cli para usar directorios dentro del proyecto (persisten en Render)
export ARDUINO_DATA_DIR="${PROJECT_DIR}/arduino-data"
export ARDUINO_DOWNLOADS_DIR="${PROJECT_DIR}/arduino-data/staging"
export ARDUINO_SKETCHBOOK_DIR="${PROJECT_DIR}/sketches"

echo "==> Configurando arduino-cli (usando directorio del proyecto)..."
echo "    ARDUINO_DATA_DIR: $ARDUINO_DATA_DIR"
./bin/arduino-cli config init --overwrite --dest-dir "${PROJECT_DIR}"

# Actualizar la configuración para usar rutas del proyecto
./bin/arduino-cli config set directories.data "${ARDUINO_DATA_DIR}"
./bin/arduino-cli config set directories.downloads "${ARDUINO_DOWNLOADS_DIR}"
./bin/arduino-cli config set directories.user "${ARDUINO_SKETCHBOOK_DIR}"

echo "==> Instalando core de Arduino AVR..."
./bin/arduino-cli core update-index
./bin/arduino-cli core install arduino:avr

echo "==> Verificando cores instalados..."
./bin/arduino-cli core list

echo "==> Build completado!"
echo "    arduino-cli instalado en: ${PROJECT_DIR}/bin/arduino-cli"
echo "    Cores en: ${ARDUINO_DATA_DIR}"

