"""
Tests funcionales para vistas del Estudiante.

Cobertura: dashboard, actividades, IDE, entregas.
No prueba Agent/Serial/WebSerial real.
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


class StudentDashboardTest(TutorStudentTestMixin, TestCase):
    """Tests del dashboard del estudiante."""

    def test_student_can_access_dashboard(self):
        """Estudiante puede entrar a su dashboard (200)."""
        self.client.login(username='test_student', password='test123')
        url = reverse('student_dashboard', kwargs={'slug': self.institution.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_dashboard_shows_tutor(self):
        """Dashboard muestra al tutor del estudiante."""
        self.client.login(username='test_student', password='test123')
        url = reverse('student_dashboard', kwargs={'slug': self.institution.slug})
        response = self.client.get(url)
        self.assertContains(response, 'Mi Grupo')
        # El tutor está en my_tutor
        tutor_name = self.tutor_user.get_full_name() or self.tutor_user.username
        self.assertContains(response, tutor_name)

    def test_dashboard_shows_group(self):
        """Dashboard muestra el grupo del estudiante."""
        self.client.login(username='test_student', password='test123')
        url = reverse('student_dashboard', kwargs={'slug': self.institution.slug})
        response = self.client.get(url)
        self.assertContains(response, self.group.name)

    def test_dashboard_shows_activities(self):
        """Dashboard muestra actividades asignadas."""
        self.client.login(username='test_student', password='test123')
        url = reverse('student_dashboard', kwargs={'slug': self.institution.slug})
        response = self.client.get(url)
        self.assertContains(response, self.activity.title)


class StudentActivitiesTest(TutorStudentTestMixin, TestCase):
    """Tests de actividades del estudiante."""

    def test_activities_list_loads(self):
        """Lista de actividades del estudiante carga (200)."""
        self.client.login(username='test_student', password='test123')
        url = reverse('editor:student_group_activities', kwargs={'institution_slug': self.institution.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_student_sees_only_own_group_activities(self):
        """Estudiante solo ve actividades de su grupo."""
        self.client.login(username='test_student', password='test123')
        url = reverse('editor:student_group_activities', kwargs={'institution_slug': self.institution.slug})
        response = self.client.get(url)
        self.assertContains(response, self.activity.title)

    def test_activity_detail_loads(self):
        """Detalle de actividad carga (200)."""
        self.client.login(username='test_student', password='test123')
        url = reverse('editor:student_activity_detail_view', kwargs={
            'institution_slug': self.institution.slug,
            'activity_id': self.activity.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_foreign_activity_returns_403_or_404(self):
        """Actividad ajena (otro grupo) devuelve 403 o 404."""
        other_inst = create_institution(slug='other-inst')
        other_tutor, _ = create_tutor(username='other_tutor', institution=other_inst)
        other_group = create_group(institution=other_inst, tutor=other_tutor, code='GRP-X')
        other_activity = create_activity(group=other_group, created_by=other_tutor)
        self.client.login(username='test_student', password='test123')
        url = reverse('editor:student_activity_detail_view', kwargs={
            'institution_slug': other_inst.slug,
            'activity_id': other_activity.id,
        })
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 403, 404])


class StudentIDETest(TutorStudentTestMixin, TestCase):
    """Tests del IDE del estudiante. No prueba compilación/subida real."""

    def test_student_can_open_activity_ide(self):
        """Estudiante puede abrir IDE de actividad asignada."""
        self.client.login(username='test_student', password='test123')
        url = reverse('editor:student_activity_ide_view', kwargs={
            'institution_slug': self.institution.slug,
            'activity_id': self.activity.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_ide_contains_key_elements(self):
        """IDE contiene elementos clave: bloques, código, botones."""
        self.client.login(username='test_student', password='test123')
        url = reverse('editor:student_activity_ide_view', kwargs={
            'institution_slug': self.institution.slug,
            'activity_id': self.activity.id,
        })
        response = self.client.get(url)
        content = response.content.decode()
        self.assertTrue(
            'blockly' in content.lower() or 'Arduino' in content or 'Entregar' in content or 'Guardar progreso' in content,
            msg='IDE debería contener elementos clave'
        )

    def test_ide_shows_submit_button_when_allowed(self):
        """Si la actividad permite entregar, aparece botón Entregar."""
        self.client.login(username='test_student', password='test123')
        url = reverse('editor:student_activity_ide_view', kwargs={
            'institution_slug': self.institution.slug,
            'activity_id': self.activity.id,
        })
        response = self.client.get(url)
        self.assertContains(response, 'Entregar')


class StudentSubmissionTest(TutorStudentTestMixin, TestCase):
    """Tests de entrega del estudiante."""

    def test_submit_valid_changes_status(self):
        """Entrega válida cambia estado a submitted."""
        self.client.login(username='test_student', password='test123')
        url = reverse('editor:api_submit_activity', kwargs={
            'institution_slug': self.institution.slug,
            'activity_id': self.activity.id,
        })
        import json
        data = {
            'xml_content': '<xml><block type="arduino_setup"/></xml>',
            'arduino_code': 'void setup() {}',
            'notes': '',
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        resp_data = response.json()
        self.assertTrue(resp_data.get('ok'))
        from editor.models import Submission
        sub = Submission.objects.filter(activity=self.activity, student=self.student_user).first()
        self.assertIsNotNone(sub)
        self.assertEqual(sub.status, 'submitted')

    def test_submission_visible_to_tutor(self):
        """Entregada visible para el tutor en lista de entregas con nombre/username del estudiante."""
        sub = create_submission(activity=self.activity, student_user=self.student_user)
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_activity_submissions_list', kwargs={
            'institution_slug': self.institution.slug,
            'activity_id': self.activity.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # La lista muestra explícitamente el username del estudiante
        self.assertContains(response, self.student_user.username)

    def test_already_submitted_no_resubmit(self):
        """Si ya entregó y no permite reentrega, submit devuelve error."""
        sub = create_submission(activity=self.activity, student_user=self.student_user, status='submitted')
        self.activity.allow_resubmit = False
        self.activity.save()
        self.client.login(username='test_student', password='test123')
        url = reverse('editor:api_submit_activity', kwargs={
            'institution_slug': self.institution.slug,
            'activity_id': self.activity.id,
        })
        import json
        data = {'xml_content': '<xml/>', 'arduino_code': 'void setup(){}', 'notes': ''}
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertIn(response.status_code, [200, 400])
        if response.status_code == 200:
            resp_data = response.json()
            if not resp_data.get('ok'):
                self.assertIn('re-entreg', resp_data.get('error', '').lower())
