# Migración de emergencia: resetea contraseña del admin para recuperar acceso
# Se ejecuta una sola vez en el próximo deploy.
# Usamos get_user_model() porque el modelo histórico (apps.get_model) no tiene set_password.

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import migrations


def reset_admin_password(apps, schema_editor):
    User = get_user_model()
    try:
        admin = User.objects.get(username='admin')
        admin.set_password('admin123')
        admin.save()
    except User.DoesNotExist:
        User.objects.create_superuser(
            username='admin',
            email='admin@maxide.com',
            password='admin123',
            first_name='Admin',
            last_name='MAX-IDE',
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0007_add_activity_group_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(reset_admin_password, noop),
    ]
