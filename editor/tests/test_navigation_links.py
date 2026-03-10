"""
Tests de navegación y botones.

Objetivo: detectar NoReverseMatch, templates rotos, links a rutas inexistentes.
Verifica que vistas rendericen 200 y contengan botones/enlaces esperados.
"""
from django.test import TestCase, Client
from django.urls import reverse

from .test_factories import (
    TutorStudentTestMixin,
    create_submission,
)


class TutorNavigationTest(TutorStudentTestMixin, TestCase):
    """Navegación y enlaces del tutor."""

    def test_dashboard_renders_without_error(self):
        """Dashboard tutor renderiza sin excepción."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('tutor_dashboard', kwargs={'slug': self.institution.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_dashboard_contains_ver_todos(self):
        """Dashboard contiene enlace 'Ver todos'."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('tutor_dashboard', kwargs={'slug': self.institution.slug})
        response = self.client.get(url)
        self.assertContains(response, 'Ver todos')

    def test_group_detail_renders_without_error(self):
        """Detalle de grupo renderiza sin excepción."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_group_detail', kwargs={
            'institution_slug': self.institution.slug,
            'group_id': self.group.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_group_detail_contains_add_student_reference(self):
        """Detalle de grupo contiene referencia a agregar estudiante."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_group_detail', kwargs={
            'institution_slug': self.institution.slug,
            'group_id': self.group.id,
        })
        response = self.client.get(url)
        content = response.content.decode()
        self.assertTrue(
            'Agregar' in content or 'Estudiante' in content or 'Nuevo' in content,
            msg='Debería haber referencia a agregar estudiante'
        )

    def test_students_list_renders_without_error(self):
        """Lista de estudiantes renderiza sin excepción."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_students_list', kwargs={'institution_slug': self.institution.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_students_list_contains_nuevo_estudiante(self):
        """Lista de estudiantes contiene 'Nuevo Estudiante' o similar."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_students_list', kwargs={'institution_slug': self.institution.slug})
        response = self.client.get(url)
        content = response.content.decode()
        self.assertTrue(
            'Nuevo' in content or 'Estudiante' in content or 'Crear' in content,
            msg='Debería haber botón para nuevo estudiante'
        )


class StudentNavigationTest(TutorStudentTestMixin, TestCase):
    """Navegación y enlaces del estudiante."""

    def test_dashboard_renders_without_error(self):
        """Dashboard estudiante renderiza sin excepción."""
        self.client.login(username='test_student', password='test123')
        url = reverse('student_dashboard', kwargs={'slug': self.institution.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_activities_list_renders_without_error(self):
        """Lista de actividades del estudiante renderiza sin excepción."""
        self.client.login(username='test_student', password='test123')
        url = reverse('editor:student_group_activities', kwargs={'institution_slug': self.institution.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_activity_ide_renders_without_error(self):
        """IDE del estudiante renderiza sin excepción."""
        self.client.login(username='test_student', password='test123')
        url = reverse('editor:student_activity_ide_view', kwargs={
            'institution_slug': self.institution.slug,
            'activity_id': self.activity.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_activity_ide_contains_entregar(self):
        """IDE contiene 'Entregar' cuando aplica."""
        self.client.login(username='test_student', password='test123')
        url = reverse('editor:student_activity_ide_view', kwargs={
            'institution_slug': self.institution.slug,
            'activity_id': self.activity.id,
        })
        response = self.client.get(url)
        self.assertContains(response, 'Entregar')

    def test_activity_ide_contains_mis_grupos_or_activity_context(self):
        """IDE contiene elementos de contexto."""
        self.client.login(username='test_student', password='test123')
        url = reverse('editor:student_activity_ide_view', kwargs={
            'institution_slug': self.institution.slug,
            'activity_id': self.activity.id,
        })
        response = self.client.get(url)
        content = response.content.decode()
        self.assertTrue(
            'Arduino' in content or 'MAX-IDE' in content or 'Bloques' in content,
            msg='IDE debería contener elementos de contexto'
        )


class URLReverseTest(TutorStudentTestMixin, TestCase):
    """Verificar que las URLs principales hacen reverse correctamente (no NoReverseMatch)."""

    def test_tutor_urls_reverse(self):
        """Todas las URLs del tutor hacen reverse sin error."""
        urls_to_test = [
            ('editor:tutor_groups_list', {'institution_slug': self.institution.slug}),
            ('editor:tutor_group_detail', {'institution_slug': self.institution.slug, 'group_id': self.group.id}),
            ('editor:tutor_students_list', {'institution_slug': self.institution.slug}),
            ('editor:tutor_activity_submissions_list', {'institution_slug': self.institution.slug, 'activity_id': self.activity.id}),
        ]
        for name, kwargs in urls_to_test:
            try:
                url = reverse(name, kwargs=kwargs)
                self.assertIsNotNone(url)
            except Exception as e:
                self.fail(f'NoReverseMatch o error en {name}: {e}')

    def test_student_urls_reverse(self):
        """Todas las URLs del estudiante hacen reverse sin error."""
        urls_to_test = [
            ('editor:student_group_activities', {'institution_slug': self.institution.slug}),
            ('editor:student_activity_detail_view', {'institution_slug': self.institution.slug, 'activity_id': self.activity.id}),
            ('editor:student_activity_ide_view', {'institution_slug': self.institution.slug, 'activity_id': self.activity.id}),
        ]
        for name, kwargs in urls_to_test:
            try:
                url = reverse(name, kwargs=kwargs)
                self.assertIsNotNone(url)
            except Exception as e:
                self.fail(f'NoReverseMatch o error en {name}: {e}')

    def test_submission_urls_reverse(self):
        """URLs de submission hacen reverse correctamente."""
        sub = create_submission(activity=self.activity, student_user=self.student_user)
        urls_to_test = [
            ('editor:tutor_submission_detail', {'institution_slug': self.institution.slug, 'submission_id': sub.id}),
            ('editor:tutor_submission_grade_form', {'institution_slug': self.institution.slug, 'submission_id': sub.id}),
            ('editor:tutor_submission_ide_readonly_groups', {'institution_slug': self.institution.slug, 'submission_id': sub.id}),
        ]
        for name, kwargs in urls_to_test:
            try:
                url = reverse(name, kwargs=kwargs)
                self.assertIsNotNone(url)
            except Exception as e:
                self.fail(f'NoReverseMatch o error en {name}: {e}')
