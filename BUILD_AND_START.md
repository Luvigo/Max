# 🚀 MAX-IDE - Comandos de Build y Start

## 📦 Build (Instalación)

### Opción 1: Script automático
```bash
./build.sh
```

### Opción 2: Manual
```bash
# 1. Crear entorno virtual
python3 -m venv venv

# 2. Activar entorno virtual
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar migraciones
python manage.py migrate

# 5. Crear superusuario (opcional)
python manage.py createsuperuser
```

## ▶️ Start (Iniciar servidor)

### Para desarrollo local (localhost):
```bash
./start_https.sh
```
**URL:** https://localhost:8443

### Para acceso en red (desde otros PCs):
```bash
./start_https_network.sh
```
**URLs:**
- Local: https://localhost:8443
- Red: https://TU_IP:8443

### Comando directo (sin script):
```bash
# Activar entorno virtual
source venv/bin/activate

# Iniciar servidor HTTPS
python manage.py runserver_plus \
    --cert-file ssl/network.crt \
    --key-file ssl/network.key \
    0.0.0.0:8443
```

## 📋 Requisitos previos

- Python 3.8+
- pip
- arduino-cli (opcional, para compilación en servidor)
- OpenSSL o mkcert (para certificados SSL)

## 🔧 Configuración adicional

### Instalar arduino-cli (opcional):
```bash
# Linux
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
sudo mv bin/arduino-cli /usr/local/bin/

# O descargar desde: https://arduino.github.io/arduino-cli/
```

### Generar certificados SSL mejorados (mkcert):
```bash
# Instalar mkcert
sudo apt install mkcert  # Ubuntu/Debian
# o
brew install mkcert      # macOS

# Generar certificados
cd ssl
mkcert -install
mkcert localhost 127.0.0.1 ::1 $(hostname -I | awk '{print $1}')
```

## 🌐 Acceso desde clientes en red

1. **Iniciar servidor en modo red:**
   ```bash
   ./start_https_network.sh
   ```

2. **Obtener IP del servidor:**
   ```bash
   hostname -I
   ```

3. **En el cliente:**
   - Abrir Chrome, Edge u Opera
   - Ir a: `https://IP_DEL_SERVIDOR:8443`
   - Aceptar certificado SSL (advertencia de seguridad)
   - Hacer clic en ➕ para agregar puerto serial del Arduino

## 📝 Notas

- **Web Serial API** requiere HTTPS (no funciona con HTTP excepto localhost)
- Solo funciona en **Chrome, Edge u Opera** (Firefox/Safari no soportan Web Serial)
- Los certificados autofirmados mostrarán advertencia de seguridad (normal en desarrollo)

