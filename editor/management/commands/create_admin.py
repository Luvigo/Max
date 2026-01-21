"""
Comando de Django para crear usuarios admin
Uso: python manage.py create_admin --username admin --email admin@example.com --password admin123
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import getpass


class Command(BaseCommand):
    help = 'Crea un usuario administrador (superuser)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Nombre de usuario (default: admin)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@maxide.com',
            help='Email del usuario (default: admin@maxide.com)',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Contraseña (si no se proporciona, se solicitará)',
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Admin',
            help='Nombre del usuario (default: Admin)',
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='MAX-IDE',
            help='Apellido del usuario (default: MAX-IDE)',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        first_name = options['first_name']
        last_name = options['last_name']
        
        # Solicitar contraseña si no se proporcionó
        password = options['password']
        if not password:
            password = getpass.getpass('Contraseña: ')
            password_confirm = getpass.getpass('Confirmar contraseña: ')
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('Las contraseñas no coinciden'))
                return
        
        # Verificar si el usuario ya existe
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Usuario admin creado exitosamente!'))
            self.stdout.write(f'   Usuario: {username}')
            self.stdout.write(f'   Email: {email}')
            self.stdout.write(f'   Password: {password}')
        else:
            # Usuario ya existe, actualizar contraseña y permisos
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.WARNING(f'→ Usuario "{username}" ya existe. Permisos y contraseña actualizados.'))
            self.stdout.write(f'   Usuario: {username}')
            self.stdout.write(f'   Email: {email}')
            self.stdout.write(f'   Password: {password}')
