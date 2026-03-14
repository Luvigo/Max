"""
Tests para auto-creación de perfiles (Student/TutorProfile) al asignar rol en Membership.

Garantiza:
- Crear user con rol estudiante => crea Student
- Cambiar rol a tutor => crea TutorProfile
- Si perfil ya existe => NO crea duplicado
- Si cambia estudiante->tutor: NO borra Student, solo crea TutorProfile

Nota: Estos tests requieren PostgreSQL (DATABASE_URL) porque la migración 0003
convierte Institution/Membership a UUID solo en PostgreSQL. En SQLite fallan
con "datatype mismatch" (schema no convertido).
"""
import unittest
from django.test import TestCase
from django.db import connection
from django.contrib.auth.models import User

from editor.models import Institution, Membership, Student, TutorProfile


def skip_if_sqlite():
    """Decorador para omitir tests en SQLite (schema usa integer, no UUID)."""
    return unittest.skipIf(
        connection.vendor == 'sqlite',
        "Migration 0003 only converts to UUID on PostgreSQL; SQLite has schema mismatch"
    )


@skip_if_sqlite()
class ProfileAutoCreationTest(TestCase):
    """Tests de auto-creación de perfiles vía signal post_save en Membership."""

    def setUp(self):
        self.institution = Institution.objects.create(
            name='Test Institution',
            slug='test-inst',
            code='TEST001',
            status='active',
        )

    def test_membership_student_creates_student_profile(self):
        """Crear Membership con rol estudiante => crea Student automáticamente."""
        user = User.objects.create_user(
            username='estudiante1',
            email='est@test.com',
            password='test123',
        )
        self.assertFalse(Student.objects.filter(user=user).exists())

        Membership.objects.create(
            user=user,
            institution=self.institution,
            role='student',
            is_active=True,
        )

        self.assertTrue(Student.objects.filter(user=user).exists())
        student = Student.objects.get(user=user)
        self.assertEqual(student.institution, self.institution)
        self.assertTrue(student.student_id.startswith('EST-'))
        self.assertTrue(student.is_active)

    def test_membership_tutor_creates_tutor_profile(self):
        """Crear Membership con rol tutor => crea TutorProfile automáticamente."""
        user = User.objects.create_user(
            username='tutor1',
            email='tutor@test.com',
            password='test123',
        )
        self.assertFalse(TutorProfile.objects.filter(user=user).exists())

        Membership.objects.create(
            user=user,
            institution=self.institution,
            role='tutor',
            is_active=True,
        )

        self.assertTrue(TutorProfile.objects.filter(user=user).exists())
        profile = TutorProfile.objects.get(user=user)
        self.assertEqual(profile.institution, self.institution)
        self.assertEqual(profile.status, 'active')

    def test_existing_profile_not_duplicated(self):
        """Si el perfil ya existe, NO se crea duplicado."""
        user = User.objects.create_user(
            username='estudiante2',
            email='est2@test.com',
            password='test123',
        )
        Student.objects.create(
            user=user,
            student_id='EST-MANUAL-001',
            institution=self.institution,
            is_active=True,
        )
        count_before = Student.objects.filter(user=user).count()

        Membership.objects.create(
            user=user,
            institution=self.institution,
            role='student',
            is_active=True,
        )

        count_after = Student.objects.filter(user=user).count()
        self.assertEqual(count_before, count_after)
        self.assertEqual(count_after, 1)
        # El estudiante original se mantiene (no se sobrescribe)
        student = Student.objects.get(user=user)
        self.assertEqual(student.student_id, 'EST-MANUAL-001')

    def test_change_role_to_tutor_creates_tutor_profile(self):
        """Cambiar rol a tutor (desde otro rol) => crea TutorProfile."""
        user = User.objects.create_user(
            username='usuario_mixto',
            email='mix@test.com',
            password='test123',
        )
        membership = Membership.objects.create(
            user=user,
            institution=self.institution,
            role='student',
            is_active=True,
        )
        self.assertTrue(Student.objects.filter(user=user).exists())
        self.assertFalse(TutorProfile.objects.filter(user=user).exists())

        # Cambiar rol a tutor
        membership.role = 'tutor'
        membership.save()

        self.assertTrue(TutorProfile.objects.filter(user=user).exists())
        # NO se borra el Student (decisión de negocio documentada)
        self.assertTrue(Student.objects.filter(user=user).exists())

    def test_student_to_tutor_keeps_student_profile(self):
        """Si cambia estudiante->tutor: NO borra Student, solo crea TutorProfile."""
        user = User.objects.create_user(
            username='cambio_rol',
            email='cambio@test.com',
            password='test123',
        )
        membership = Membership.objects.create(
            user=user,
            institution=self.institution,
            role='student',
            is_active=True,
        )
        student = Student.objects.get(user=user)
        student_id_original = student.student_id

        membership.role = 'tutor'
        membership.save()

        # Student sigue existiendo
        self.assertTrue(Student.objects.filter(user=user).exists())
        student_after = Student.objects.get(user=user)
        self.assertEqual(student_after.student_id, student_id_original)

        # TutorProfile también existe
        self.assertTrue(TutorProfile.objects.filter(user=user).exists())
