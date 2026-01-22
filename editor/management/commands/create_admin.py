"""
Comando de Django para crear usuarios admin
Uso: python manage.py create_admin --username admin --email admin@example.com --password admin123

NOTA: Este comando SOLO crea el usuario si NO existe.
Si el usuario ya existe, NO modifica nada (preserva contraseña y datos).
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import getpass


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
