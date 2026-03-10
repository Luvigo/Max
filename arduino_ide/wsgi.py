"""
WSGI config for arduino_ide project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/

DEMO_SEED_SOURCE: ANTES se recreaban usuarios demo aquí (create_initial_users al importar).
  Ahora NO hay auto-seed. Los usuarios demo solo se crean con:
  SEED_DEMO_DATA=1 python manage.py seed_demo_data
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arduino_ide.settings')

application = get_wsgi_application()

# Log de verificación: en producción nunca se crean usuarios demo automáticamente.
if os.environ.get('RENDER') == 'true' or os.environ.get('ENV', '').lower() in ('production', 'prod', 'staging'):
    print("[DEMO_SEED] disabled (ENV=production)")