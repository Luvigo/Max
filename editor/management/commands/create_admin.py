"""
Comando de Django para crear usuarios admin.
Uso: python manage.py create_admin --username admin --email admin@example.com --password admin123

NOTA: Este comando SOLO crea el usuario si NO existe.
Si el usuario ya existe, NO modifica nada (preserva contraseña y datos).
En producción/staging, --force está deshabilitado para no resetear contraseñas.
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
import getpass
import os


class Command(BaseCommand):
    help = 'Crea un usuario administrador (superuser) SOLO si no existe'

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
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar actualización de contraseña si el usuario ya existe',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        first_name = options['first_name']
        last_name = options['last_name']
        force = options.get('force', False)

        # En producción/staging no permitir --force (evitar reseteo de contraseña)
        render = os.environ.get('RENDER') == 'true'
        env = os.environ.get('ENV', '').lower()
        if force and (render or env in ('production', 'staging')):
            raise CommandError(
                'No se puede usar --force en producción o staging. '
                'Cambia la contraseña desde Django Admin.'
            )

        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            if force:
                # Solo actualizar si se usa --force
                password = options['password']
                if not password:
                    password = getpass.getpass('Contraseña: ')
                    password_confirm = getpass.getpass('Confirmar contraseña: ')
                    if password != password_confirm:
                        self.stdout.write(self.style.ERROR('Las contraseñas no coinciden'))
                        return
                
                user = User.objects.get(username=username)
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.WARNING(f'→ Contraseña actualizada para "{username}" (--force usado).'))
            else:
                # NO modificar nada si ya existe
                self.stdout.write(self.style.SUCCESS(f'✓ Usuario "{username}" ya existe. No se modificó nada.'))
            return
        
        # El usuario NO existe, crearlo
        password = options['password']
        if not password:
            password = getpass.getpass('Contraseña: ')
            password_confirm = getpass.getpass('Confirmar contraseña: ')
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('Las contraseñas no coinciden'))
                return
        
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Usuario admin creado exitosamente!'))
        self.stdout.write(f'   Usuario: {username}')
        self.stdout.write(f'   Email: {email}')
