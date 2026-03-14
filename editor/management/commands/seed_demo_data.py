"""
Comando manual para crear usuarios demo (test_estudiante1/2/3, test_tutor, test_institucion).
Uso: SEED_DEMO_DATA=1 python manage.py seed_demo_data

DEMO_SEED_SOURCE: Este es el ÚNICO punto que crea usuarios demo.
  - NO se ejecuta automáticamente en migrate, wsgi ni AppConfig.ready.
  - En producción (RENDER/ENV=production) se rechaza.
  - Idempotente: usa get_or_create, no recrea si ya existen.
"""
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from editor.models import (
    Institution, Membership, Course, Enrollment, TeachingAssignment,
)


def _is_production():
    return (
        os.environ.get('RENDER') == 'true'
        or os.environ.get('ENV', '').lower() in ('production', 'prod', 'staging')
    )


class Command(BaseCommand):
    help = 'Crea usuarios demo (idempotente). Solo en desarrollo con SEED_DEMO_DATA=1.'

    def handle(self, *args, **options):
        if _is_production():
            self.stdout.write(self.style.WARNING('[DEMO_SEED] disabled (ENV=production or RENDER=true)'))
            raise CommandError(
                'seed_demo_data no puede ejecutarse en producción. '
                'Los usuarios se crean desde Django Admin.'
            )

        if os.environ.get('SEED_DEMO_DATA', '').strip().lower() not in ('1', 'true', 'yes'):
            self.stdout.write(self.style.WARNING('[DEMO_SEED] skipped (SEED_DEMO_DATA not set)'))
            raise CommandError(
                'Para ejecutar: SEED_DEMO_DATA=1 python manage.py seed_demo_data'
            )

        created_count = self._run_seed()
        self.stdout.write(self.style.SUCCESS(f'[DEMO_SEED] created {created_count} user(s)'))

    def _run_seed(self):
        """Lógica idempotente. Retorna número de usuarios creados."""
        created_count = 0

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@maxide.com',
                password='admin123',
                first_name='Admin',
                last_name='MAX-IDE'
            )
            created_count += 1
            self.stdout.write('  + admin')

        institution, inst_created = Institution.objects.get_or_create(
            slug='test-institucion',
            defaults={
                'name': 'Institución de Prueba',
                'code': 'TEST001',
                'status': 'active',
            }
        )
        if inst_created:
            created_count += 1
            self.stdout.write('  + test-institucion')

        test_users = [
            ('test_admin', 'admin@test.com', 'Admin', 'Test', True, True, None),
            ('test_institucion', 'institucion@test.com', 'Institución', 'Test', False, False, 'institution'),
            ('test_tutor', 'tutor@test.com', 'Profesor', 'Test', False, False, 'tutor'),
            ('test_estudiante1', 'estudiante1@test.com', 'Estudiante', '1', False, False, 'student'),
            ('test_estudiante2', 'estudiante2@test.com', 'Estudiante', '2', False, False, 'student'),
            ('test_estudiante3', 'estudiante3@test.com', 'Estudiante', '3', False, False, 'student'),
        ]

        for username, email, first_name, last_name, is_staff, is_superuser, role in test_users:
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_staff': is_staff,
                    'is_superuser': is_superuser,
                }
            )
            if user_created:
                user.set_password('test123')
                user.save()
                created_count += 1
                self.stdout.write(f'  + {username}')
            elif not user.has_usable_password():
                user.set_password('test123')
                user.save()

            if role:
                Membership.objects.get_or_create(
                    user=user,
                    institution=institution,
                    defaults={'role': role, 'is_active': True}
                )

        tutor_user = User.objects.filter(username='test_tutor').first()
        course, course_created = Course.objects.get_or_create(
            institution=institution,
            code='ARDUINO101',
            defaults={
                'name': 'Programación con Arduino',
                'description': 'Curso introductorio de Arduino',
                'grade_level': '1ro',
                'academic_year': '2024',
                'status': 'published',
                'tutor': tutor_user,
            }
        )
        if course_created:
            if tutor_user:
                TeachingAssignment.objects.get_or_create(
                    course=course,
                    tutor=tutor_user,
                    defaults={'status': 'active'}
                )
            for i in range(1, 4):
                student_user = User.objects.filter(username=f'test_estudiante{i}').first()
                if student_user:
                    Enrollment.objects.get_or_create(
                        course=course,
                        student=student_user,
                        defaults={'status': 'active'}
                    )

        return created_count
