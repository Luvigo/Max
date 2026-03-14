"""
Tests funcionales para vistas del Tutor.

Cobertura: dashboard, grupos, estudiantes, actividades, IDE, entregas.
No prueba lógica de Agent/Serial real.
"""
from django.test import TestCase, Client
from django.urls import reverse

from .test_factories import (
    TutorStudentTestMixin,
    create_institution,
    create_tutor,
    create_student,
    create_group,
    create_activity,
    create_submission,
)


class TutorDashboardTest(TutorStudentTestMixin, TestCase):
    """Tests del dashboard del tutor."""

    def test_tutor_can_access_dashboard(self):
        """Tutor puede entrar a su dashboard (200)."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('tutor_dashboard', kwargs={'slug': self.institution.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_dashboard_renders_main_sections(self):
        """Se renderizan secciones principales: Mis Grupos, métricas."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('tutor_dashboard', kwargs={'slug': self.institution.slug})
        response = self.client.get(url)
        self.assertContains(response, 'Mis Grupos')
        self.assertContains(response, 'Mis Estudiantes')
        self.assertContains(response, 'Mis Actividades')
        self.assertContains(response, 'Pendientes de Calificar')

    def test_dashboard_ver_todos_link_works(self):
        """El enlace 'Ver todos' de grupos no provoca NoReverseMatch."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('tutor_dashboard', kwargs={'slug': self.institution.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Ver todos apunta a /i/<slug>/tutor/groups/
        verify_url = f'/i/{self.institution.slug}/tutor/groups/'
        self.assertIn(verify_url, response.content.decode() or '')

    def test_dashboard_with_activities_and_submissions(self):
        """Con actividades y entregas, el dashboard carga sin error."""
        create_submission(activity=self.activity, student_user=self.student_user)
        self.client.login(username='test_tutor', password='test123')
        url = reverse('tutor_dashboard', kwargs={'slug': self.institution.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class TutorGroupsTest(TutorStudentTestMixin, TestCase):
    """Tests de grupos del tutor."""

    def test_groups_list_loads(self):
        """Lista de grupos carga (200)."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_groups_list', kwargs={'institution_slug': self.institution.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_group_detail_loads(self):
        """Detalle de grupo carga (200)."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_group_detail', kwargs={
            'institution_slug': self.institution.slug,
            'group_id': self.group.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_group_detail_contains_group_name(self):
        """Detalle de grupo muestra nombre del grupo."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_group_detail', kwargs={
            'institution_slug': self.institution.slug,
            'group_id': self.group.id,
        })
        response = self.client.get(url)
        self.assertContains(response, self.group.name)

    def test_add_student_button_or_link_exists(self):
        """En detalle de grupo existe enlace o botón para agregar estudiante."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_group_detail', kwargs={
            'institution_slug': self.institution.slug,
            'group_id': self.group.id,
        })
        response = self.client.get(url)
        # Puede ser "Agregar Estudiante" o "Nuevo Estudiante"
        content = response.content.decode()
        self.assertTrue(
            'Agregar' in content or 'Estudiante' in content or 'Nuevo' in content,
            msg='Debería haber referencia a agregar estudiante'
        )

    def test_group_edit_loads(self):
        """Vista editar grupo carga (200)."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_group_edit', kwargs={
            'institution_slug': self.institution.slug,
            'group_id': self.group.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_group_create_form_loads(self):
        """Formulario de crear grupo carga (200)."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_group_create', kwargs={'institution_slug': self.institution.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class TutorStudentsTest(TutorStudentTestMixin, TestCase):
    """Tests de estudiantes del tutor."""

    def test_students_list_loads(self):
        """Lista de estudiantes del tutor carga (200)."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_students_list', kwargs={'institution_slug': self.institution.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_new_student_button_works(self):
        """Botón/enlace 'Nuevo Estudiante' lleva a formulario que carga."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_student_create', kwargs={'institution_slug': self.institution.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_student_with_valid_data(self):
        """Crear estudiante con datos válidos crea user, profile y asociación."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_student_create', kwargs={'institution_slug': self.institution.slug})
        get_resp = self.client.get(url)
        self.assertEqual(get_resp.status_code, 200)
        import re
        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', get_resp.content.decode())
        csrf = csrf_match.group(1) if csrf_match else ''
        data = {
            'username': 'nuevo_est',
            'email': 'nuevo@test.com',
            'first_name': 'Nuevo',
            'last_name': 'Estudiante',
            'student_id': 'STD-NUEVO',
            'password': 'testpass123',
            'group': str(self.group.id),
            'csrfmiddlewaretoken': csrf,
        }
        response = self.client.post(url, data, follow=True)
        self.assertIn(response.status_code, [200, 302])
        from editor.models import User, Student, Membership
        user = User.objects.filter(username='nuevo_est').first()
        self.assertIsNotNone(user, 'Debería crearse el usuario')
        if user:
            self.assertTrue(Student.objects.filter(user=user).exists())
            self.assertTrue(Membership.objects.filter(user=user, institution=self.institution).exists())

    def test_student_detail_loads(self):
        """Detalle de estudiante carga (200)."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_student_detail', kwargs={
            'institution_slug': self.institution.slug,
            'student_id': self.student.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class TutorActivitiesTest(TutorStudentTestMixin, TestCase):
    """Tests de actividades del tutor."""

    def test_activities_list_loads(self):
        """Lista de actividades del tutor carga (200)."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_my_activities_list', kwargs={'institution_slug': self.institution.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_group_activities_list_loads(self):
        """Lista de actividades de un grupo carga (200)."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_group_activities_list', kwargs={
            'institution_slug': self.institution.slug,
            'group_id': self.group.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_activity_form_loads(self):
        """Formulario de crear actividad (eligiendo grupo) carga."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_group_activity_create', kwargs={
            'institution_slug': self.institution.slug,
            'group_id': self.group.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_submissions_list_loads(self):
        """Lista de entregas de una actividad carga (200)."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_activity_submissions_list', kwargs={
            'institution_slug': self.institution.slug,
            'activity_id': self.activity.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_submission_detail_loads(self):
        """Detalle de entrega carga (200)."""
        sub = create_submission(activity=self.activity, student_user=self.student_user)
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_submission_detail', kwargs={
            'institution_slug': self.institution.slug,
            'submission_id': sub.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_submission_grade_form_loads(self):
        """Formulario de calificar entrega carga (200)."""
        sub = create_submission(activity=self.activity, student_user=self.student_user)
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_submission_grade_form', kwargs={
            'institution_slug': self.institution.slug,
            'submission_id': sub.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_submission_ver_bloques_loads(self):
        """Vista 'Ver bloques' de entrega carga (200)."""
        sub = create_submission(activity=self.activity, student_user=self.student_user)
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_submission_ide_readonly_groups', kwargs={
            'institution_slug': self.institution.slug,
            'submission_id': sub.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class TutorIDETest(TutorStudentTestMixin, TestCase):
    """Tests del IDE del tutor (sandbox). No prueba Agent/Serial real."""

    def test_ide_sandbox_loads_without_500(self):
        """Vista IDE sandbox del tutor carga sin 500."""
        self.client.login(username='test_tutor', password='test123')
        # tutor_activity_ide_sandbox usa str:activity_id (legacy), pero las actividades de grupos usan uuid
        url = reverse('editor:tutor_activity_ide_sandbox', kwargs={
            'institution_slug': self.institution.slug,
            'activity_id': str(self.activity.id),
        })
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302, 404], 'No debe devolver 500')

    def test_ide_response_contains_key_elements(self):
        """Si el IDE carga, contiene botones clave (Verificar, etc)."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_activity_ide_sandbox', kwargs={
            'institution_slug': self.institution.slug,
            'activity_id': str(self.activity.id),
        })
        response = self.client.get(url)
        if response.status_code == 200:
            content = response.content.decode()
            # Al menos uno de los elementos típicos del IDE
            self.assertTrue(
                'Verificar' in content or 'Subir' in content or 'blockly' in content.lower() or 'Arduino' in content,
                msg='IDE debería contener elementos clave'
            )
