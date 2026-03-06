# Migración de emergencia: resetea contraseña del admin para recuperar acceso
# Se ejecuta una sola vez en el próximo deploy.

from django.conf import settings
from django.db import migrations


def reset_admin_password(apps, schema_editor):
    app_label, model_name = settings.AUTH_USER_MODEL.split('.')
    User = apps.get_model(app_label, model_name)
    try:
        admin = User.objects.get(username='admin')
        admin.set_password('admin123')
        admin.save()
    except User.DoesNotExist:
        admin = User(
            username='admin',
            email='admin@maxide.com',
            first_name='Admin',
            last_name='MAX-IDE',
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        admin.set_password('admin123')
        admin.save()


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
