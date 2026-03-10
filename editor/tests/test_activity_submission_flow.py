"""
Tests de flujo de actividades y entregas.

Integración básica entre tutor, estudiante, actividades y submissions.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import json

from .test_factories import (
    TutorStudentTestMixin,
    create_activity,
    create_submission,
)


class ActivitySubmissionFlowTest(TutorStudentTestMixin, TestCase):
    """Flujo completo actividad -> entrega -> calificación."""

    def test_tutor_creates_activity_student_sees_it(self):
        """Tutor crea actividad, estudiante la ve en su lista."""
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_group_activity_create', kwargs={
            'institution_slug': self.institution.slug,
            'group_id': self.group.id,
        })
        get_resp = self.client.get(url)
        self.assertEqual(get_resp.status_code, 200)
        import re
        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', get_resp.content.decode())
        csrf = csrf_match.group(1) if csrf_match else ''
        deadline_str = (timezone.now() + timezone.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M')
        data = {
            'title': 'Actividad Nueva Test',
            'objective': 'Objetivo test',
            'instructions': 'Instrucciones detalladas',
            'deadline': deadline_str,
            'status': 'published',
            'max_score': 10,
            'allow_resubmit': 'on',
            'csrfmiddlewaretoken': csrf,
        }
        response = self.client.post(url, data, follow=True)
        self.assertIn(response.status_code, [200, 302])
        from editor.models import Activity
        act = Activity.objects.filter(group=self.group, title='Actividad Nueva Test').first()
        self.assertIsNotNone(act, 'Debería crearse la actividad')
        if act:
            self.client.logout()
            self.client.login(username='test_student', password='test123')
            list_url = reverse('editor:student_group_activities', kwargs={'institution_slug': self.institution.slug})
            list_resp = self.client.get(list_url)
            self.assertContains(list_resp, 'Actividad Nueva Test')

    def test_student_submits_tutor_sees_submission(self):
        """Estudiante entrega, tutor ve la entrega en la lista."""
        self.client.login(username='test_student', password='test123')
        submit_url = reverse('editor:api_submit_activity', kwargs={
            'institution_slug': self.institution.slug,
            'activity_id': self.activity.id,
        })
        data = {
            'xml_content': '<xml><block type="arduino_setup"/></xml>',
            'arduino_code': 'void setup() {}',
            'notes': 'Nota test',
        }
        self.client.post(submit_url, data=json.dumps(data), content_type='application/json')
        self.client.logout()
        self.client.login(username='test_tutor', password='test123')
        list_url = reverse('editor:tutor_activity_submissions_list', kwargs={
            'institution_slug': self.institution.slug,
            'activity_id': self.activity.id,
        })
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        # La lista muestra explícitamente el username del estudiante
        self.assertContains(response, self.student_user.username)

    def test_tutor_can_grade_submission(self):
        """Tutor puede calificar una entrega."""
        sub = create_submission(activity=self.activity, student_user=self.student_user)
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_submission_grade_form', kwargs={
            'institution_slug': self.institution.slug,
            'submission_id': sub.id,
        })
        # Obtener CSRF token desde el formulario
        get_resp = self.client.get(url)
        self.assertEqual(get_resp.status_code, 200)
        import re
        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', get_resp.content.decode())
        csrf_token = csrf_match.group(1) if csrf_match else ''
        response = self.client.post(url, {
            'score': 8,
            'comments': 'Buen trabajo',
            'csrfmiddlewaretoken': csrf_token,
        }, follow=True)
        self.assertIn(response.status_code, [200, 302])
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'graded')
        self.assertEqual(float(sub.score), 8.0)

    def test_tutor_can_view_submission_blocks(self):
        """Tutor puede ver bloques Blockly de una entrega."""
        sub = create_submission(activity=self.activity, student_user=self.student_user)
        self.client.login(username='test_tutor', password='test123')
        url = reverse('editor:tutor_submission_ide_readonly_groups', kwargs={
            'institution_slug': self.institution.slug,
            'submission_id': sub.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Solo lectura')
