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

## 🌱 Seed de usuarios demo

**DEMO_SEED_SOURCE:** Los usuarios demo se recreaban en `arduino_ide/wsgi.py` al cargar el WSGI (gunicorn Start Command). Ya no hay auto-seed.

**Fix:** El seed se movió a comando manual: `SEED_DEMO_DATA=1 python manage.py seed_demo_data`. En producción nunca se ejecuta. En los logs verás `[DEMO_SEED] disabled (ENV=production)`.

## 🔧 Configuración en Render Dashboard

### Variables de Entorno Requeridas:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `SECRET_KEY` | (generar nuevo) | Secret key de Django para producción |
| `DEBUG` | `False` | Desactivar modo debug |
| `ALLOWED_HOSTS` | `tu-app.onrender.com` | Tu dominio de Render |
| **`DATABASE_URL`** | *(PostgreSQL de Render)* | **OBLIGATORIO en producción.** Sin esto se usa SQLite en disco efímero: la base de datos se borra en cada deploy y se pierden usuarios y credenciales. |
| `RENDER` | `true` | Detecta que está en Render (opcional, se detecta automáticamente) |
| `ENV` | `production` | Recomendado. Evita que seed_demo_data corra. Usuarios se crean desde Django Admin. |
| `SEED_DEMO_DATA` | *(no configurar)* | **NO** configurar en producción. Solo para desarrollo local. |

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

## 🗄️ Base de datos y persistencia (crítico)

**En producción debes usar una base de datos persistente.**

- **Recomendado:** Crear un **PostgreSQL** en Render (Dashboard → New → PostgreSQL) y añadir la variable de entorno **`DATABASE_URL`** que Render te da. Así la base de datos persiste entre deploys.
- **Sin `DATABASE_URL`:** Django usa SQLite (`db.sqlite3`). En Render el sistema de archivos del servicio es **efímero**: en cada deploy se pierde el archivo y la base de datos se recrea vacía. Eso provoca:
  - Pérdida de todos los usuarios creados
  - Reseteo de la contraseña del admin a la del primer deploy
  - Reaparición aparente de “usuarios de prueba” si SEED_DEMO_DATA=1 está configurada (en producción no debe estar)

**Regla:** No uses SQLite en producción en Render. Configura siempre `DATABASE_URL` (PostgreSQL) para que usuarios y credenciales persistan.

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

### Usuarios de prueba reaparecen después de cada deploy
- **Causa:** El seed se ejecutaba en wsgi.py al arrancar. Ahora está bloqueado si `RENDER=true` (automático en Render) o `ENV=production`.
- **Solución:** Configura `ENV=production` en Render si aún ves usuarios demo. Elimina `SEED_DEMO_DATA` si está configurada.

### Usuarios o contraseñas se pierden después de cada deploy
- **Causa:** No hay `DATABASE_URL` y se está usando SQLite en disco efímero.
- **Solución:** Crea una base PostgreSQL en Render y configura la variable `DATABASE_URL`. Tras el siguiente deploy, los usuarios y credenciales persistirán.

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

