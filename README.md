# ⚡ MAX-IDE - Arduino Block Editor

IDE de programación visual para Arduino basado en Blockly, con compilación en servidor y subida directa desde el navegador usando Web Serial API.

## 🚀 Inicio Rápido

### Build (Primera vez)
```bash
./build.sh
```

### Start (Iniciar servidor)

**Local (localhost):**
```bash
./start_https.sh
```
→ https://localhost:8443

**Red (acceso desde otros PCs):**
```bash
./start_https_network.sh
```
→ https://TU_IP:8443

## 📋 Comandos Principales

### Build
```bash
# Automático
./build.sh

# Manual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

### Start
```bash
# Local
./start_https.sh

# Red
./start_https_network.sh
```

### Otros comandos útiles
```bash
# Crear superusuario
source venv/bin/activate
python manage.py createsuperuser

# Ejecutar migraciones
python manage.py migrate

# Shell de Django
python manage.py shell
```

## ✨ Características

- 🧩 **Editor de Bloques Visual** - Basado en Blockly
- 🔌 **Web Serial API** - Sube código directamente desde el navegador
- 🌐 **Acceso en Red** - Múltiples clientes pueden conectarse
- ⚙️ **Compilación en Servidor** - El servidor compila, el cliente sube
- 📟 **Monitor Serial** - Integrado en el IDE
- 💾 **Sistema de Proyectos** - Guarda y carga proyectos
- 🔐 **Autenticación** - Sistema de usuarios y permisos

## 🔧 Requisitos

- **Python 3.8+**
- **pip**
- **arduino-cli** (opcional, para compilación en servidor)
- **Navegador:** Chrome, Edge u Opera (para Web Serial API)

## 📖 Documentación

- [BUILD_AND_START.md](BUILD_AND_START.md) - Guía detallada de build y start
- [PUSH_TO_GITHUB.md](PUSH_TO_GITHUB.md) - Instrucciones para subir a GitHub

## 🌐 Uso desde Red

1. Iniciar servidor: `./start_https_network.sh`
2. Obtener IP: `hostname -I`
3. En cliente: Abrir `https://IP:8443` en Chrome/Edge/Opera
4. Aceptar certificado SSL
5. Clic en ➕ para agregar puerto serial del Arduino

## 📝 Notas

- Web Serial API requiere **HTTPS** (no funciona con HTTP excepto localhost)
- Solo funciona en **Chrome, Edge u Opera**
- Los certificados autofirmados mostrarán advertencia (normal en desarrollo)

## 🛠️ Tecnologías

- **Backend:** Django 6.0
- **Frontend:** Blockly, JavaScript (ES6+)
- **Serial:** Web Serial API, pyserial
- **SSL:** OpenSSL / mkcert

## 📄 Licencia

Ver archivo LICENSE

