"""
Helpers / Factories mínimas para tests funcionales de Tutor y Estudiante.

Proporciona datos reutilizables: Institution, Tutor, Student, Group, Activity, Submission.
Usa los modelos existentes del proyecto (User, Student, StudentGroup, Activity, etc.).

NOTA SQLite: La migración 0003 convierte Institution/Membership a UUID solo en PostgreSQL.
En SQLite el esquema sigue con integer, causando "datatype mismatch". Los tests que usan
estas factories deben decorarse con @skip_if_sqlite() o ejecutarse con PostgreSQL.
"""
import unittest
from django.contrib.auth.models import User
from django.db import connection
from django.utils import timezone
from datetime import timedelta

from editor.models import (
    Institution, Membership, StudentGroup, Student, Activity, Submission
)


def skip_if_sqlite():
    """Decorador para omitir tests en SQLite (schema usa integer, no UUID)."""
    return unittest.skipIf(
        connection.vendor == 'sqlite',
        "Migration 0003 only converts to UUID on PostgreSQL; SQLite has schema mismatch. Use DATABASE_URL with PostgreSQL to run these tests."
    )


def create_institution(name='Test Institution', slug='test-inst', **kwargs):
    """Crear institución mínima."""
    defaults = {'name': name, 'slug': slug, 'status': 'active', 'code': slug.upper()[:8]}
    defaults.update(kwargs)
    return Institution.objects.create(**defaults)


def create_tutor(username='test_tutor', institution=None, password='test123', **kwargs):
    """Crear tutor con Membership. Retorna (user, institution)."""
    if institution is None:
        institution = create_institution()
    user = User.objects.create_user(
        username=username,
        email=f'{username}@test.com',
        password=password,
        first_name='Tutor',
        last_name='Test',
        **kwargs
    )
    Membership.objects.create(
        user=user,
        institution=institution,
        role='tutor',
        is_active=True
    )
    return user, institution


def create_student(username='test_student', institution=None, group=None, tutor=None, password='test123', **kwargs):
    """
    Crear estudiante asignado a grupo y tutor.
    Si no hay group/tutor, crea tutor y grupo primero.
    Retorna (user, student, institution, group).
    """
    if institution is None:
        institution = create_institution()
    if tutor is None:
        tutor, _ = create_tutor(username=f'tutor_{username}', institution=institution)
    if group is None:
        group = StudentGroup.objects.create(
            institution=institution,
            tutor=tutor,
            name='Grupo Test',
            code='GRP001',
            academic_year='2026',
            status='active'
        )
    user = User.objects.create_user(
        username=username,
        email=f'{username}@test.com',
        password=password,
        first_name='Estudiante',
        last_name='Test',
        **kwargs
    )
    # Crear Student ANTES de Membership: el signal post_save de Membership
    # auto-crea Student si no existe; crear primero evita duplicado.
    student = Student.objects.create(
        user=user,
        student_id=f'STD-{username[:4].upper()}',
        institution=institution,
        group=group,
        tutor=tutor,
        is_active=True
    )
    Membership.objects.create(
        user=user,
        institution=institution,
        role='student',
        is_active=True
    )
    return user, student, institution, group


def create_group(institution=None, tutor=None, name='Grupo Test', code='GRP001', **kwargs):
    """Crear grupo. Si no hay tutor, crea tutor e institución."""
    if institution is None or tutor is None:
        tutor, institution = create_tutor()
    return StudentGroup.objects.create(
        institution=institution,
        tutor=tutor,
        name=name,
        code=code,
        academic_year='2026',
        status='active',
        **kwargs
    )


def create_activity(group=None, created_by=None, title='Actividad Test', status='published', **kwargs):
    """
    Crear actividad publicada para un grupo.
    Si no hay group, crea institución, tutor y grupo.
    Retorna activity.
    """
    if group is None:
        tutor, institution = create_tutor()
        group = create_group(institution=institution, tutor=tutor)
        created_by = tutor
    if created_by is None:
        created_by = group.tutor
    defaults = {
        'group': group,
        'created_by': created_by,
        'title': title,
        'instructions': 'Instrucciones de prueba',
        'status': status,
        'deadline': timezone.now() + timedelta(days=7),
        'allow_resubmit': False,
        'max_score': 10,
    }
    if status == 'published':
        defaults['published_at'] = timezone.now()
    defaults.update(kwargs)
    return Activity.objects.create(**defaults)


def create_submission(activity=None, student_user=None, status='submitted', **kwargs):
    """
    Crear submission. activity y student_user deben existir y ser compatibles.
    Retorna submission.
    """
    if activity is None or student_user is None:
        raise ValueError('activity y student_user son requeridos')
    student = Student.objects.get(user=student_user)
    if student.group != activity.group:
        raise ValueError('El estudiante debe pertenecer al grupo de la actividad')
    defaults = {
        'activity': activity,
        'student': student_user,
        'status': status,
        'attempt': 1,
        'xml_content': '<xml><block type="arduino_setup"/></xml>',
        'arduino_code': 'void setup() {}',
    }
    if status in ('submitted', 'graded'):
        defaults['submitted_at'] = timezone.now()
    defaults.update(kwargs)
    return Submission.objects.create(**defaults)


class TutorStudentTestMixin:
    """
    Mixin que crea institución, tutor, estudiante, grupo y actividad.
    Atributos: institution, tutor_user, student_user, student, group, activity
    """
    def setUp(self):
        super().setUp()
        self.institution = create_institution()
        self.tutor_user, _ = create_tutor(institution=self.institution)
        self.group = create_group(institution=self.institution, tutor=self.tutor_user)
        self.student_user, self.student, _, _ = create_student(
            institution=self.institution,
            group=self.group,
            tutor=self.tutor_user
        )
        self.activity = create_activity(group=self.group, created_by=self.tutor_user)
