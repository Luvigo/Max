# 🚀 Despliegue en Render - MAX-IDE

Guía completa para desplegar MAX-IDE en Render.

## 📋 Comandos para Render

### Build Command:
```bash
chmod +x render_build.sh && ./render_build.sh
```

### Start Command:
```bash
gunicorn arduino_ide.wsgi:application
```

> **Nota:** El script `render_build.sh` instala Python deps, arduino-cli y los cores de Arduino AVR.

## 🔧 Configuración en Render Dashboard

### Variables de Entorno Requeridas:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `SECRET_KEY` | (generar nuevo) | Secret key de Django para producción |
| `DEBUG` | `False` | Desactivar modo debug |
| `ALLOWED_HOSTS` | `tu-app.onrender.com` | Tu dominio de Render |
| `RENDER` | `true` | Detecta que está en Render (opcional, se detecta automáticamente) |

### Generar SECRET_KEY:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

O usar este comando en tu terminal local:
```bash
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 📝 Pasos de Despliegue

1. **Crear nuevo Web Service en Render**
   - Conectar tu repositorio de GitHub
   - Seleccionar la rama `main`

2. **Configurar el servicio:**
   - **Name:** `max-ide` (o el nombre que prefieras)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`
   - **Start Command:** `gunicorn arduino_ide.wsgi:application`

3. **Agregar Variables de Entorno:**
   - `SECRET_KEY`: (generar uno nuevo)
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `tu-app.onrender.com` (reemplazar con tu dominio)

4. **Desplegar:**
   - Render detectará automáticamente los cambios
   - El build se ejecutará automáticamente
   - El servicio estará disponible en `https://tu-app.onrender.com`

## ⚙️ Configuración Automática

El proyecto está configurado para detectar automáticamente si está corriendo en Render:

- ✅ Detecta `RENDER=true` automáticamente
- ✅ Activa HTTPS y seguridad SSL automáticamente
- ✅ Configura `STATIC_ROOT` para archivos estáticos
- ✅ Usa variables de entorno para configuración sensible

## 🔒 Seguridad

En Render, el proyecto automáticamente:
- ✅ Activa `SECURE_SSL_REDIRECT`
- ✅ Activa `SESSION_COOKIE_SECURE`
- ✅ Activa `CSRF_COOKIE_SECURE`
- ✅ Configura `SECURE_PROXY_SSL_HEADER` para el proxy de Render

## 📦 Archivos Estáticos

Los archivos estáticos se recopilan automáticamente durante el build con:
```bash
python manage.py collectstatic --noinput
```

Render servirá estos archivos automáticamente desde `/static/`.

## 🌐 Web Serial API

Render proporciona HTTPS automáticamente, por lo que Web Serial API funcionará correctamente. Los clientes deben:

1. Abrir la URL de Render en Chrome, Edge u Opera
2. Hacer clic en ➕ para agregar su puerto serial local
3. El Arduino debe estar conectado al PC del cliente (no al servidor)

## 🐛 Troubleshooting

### Error: "DisallowedHost"
- Verifica que `ALLOWED_HOSTS` incluya tu dominio de Render
- Formato: `tu-app.onrender.com` (sin https://)

### Error: "Static files not found"
- Verifica que el build command incluya `collectstatic`
- Los archivos estáticos se recopilan en `staticfiles/`

### Error: "SECRET_KEY not set"
- Agrega la variable de entorno `SECRET_KEY` en Render
- Genera uno nuevo con el comando proporcionado arriba

## 📊 Monitoreo

Render proporciona:
- Logs en tiempo real
- Métricas de rendimiento
- Alertas automáticas

Revisa los logs en el dashboard de Render si hay problemas.

