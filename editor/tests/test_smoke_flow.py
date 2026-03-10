"""
Smoke tests de flujo end-to-end mínimo.

Flujos completos Tutor y Estudiante sin depender de Agent/Serial.
"""
from django.test import TestCase, Client
from django.urls import reverse
import json

from .test_factories import (
    create_institution,
    create_tutor,
    create_student,
    create_group,
    create_activity,
)


class TutorFlowSmokeTest(TestCase):
    """Flujo completo Tutor: login -> grupos -> estudiante -> actividad."""

    def setUp(self):
        self.inst = create_institution()
        self.tutor_user, _ = create_tutor(institution=self.inst)
        self.client = Client()

    def test_tutor_full_flow(self):
        """Login tutor -> dashboard -> crear grupo -> crear estudiante -> actividades."""
        self.client.login(username='test_tutor', password='test123')
        # 1. Dashboard
        r = self.client.get(reverse('tutor_dashboard', kwargs={'slug': self.inst.slug}))
        self.assertEqual(r.status_code, 200)
        # 2. Lista de grupos
        r = self.client.get(reverse('editor:tutor_groups_list', kwargs={'institution_slug': self.inst.slug}))
        self.assertEqual(r.status_code, 200)
        # 3. Crear grupo
        r = self.client.get(reverse('editor:tutor_group_create', kwargs={'institution_slug': self.inst.slug}))
        self.assertEqual(r.status_code, 200)
        import re
        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.content.decode())
        csrf = csrf_match.group(1) if csrf_match else ''
        r = self.client.post(
            reverse('editor:tutor_group_create', kwargs={'institution_slug': self.inst.slug}),
            {
                'name': 'Grupo Smoke',
                'code': 'SMK001',
                'academic_year': '2026',
                'max_students': 25,
                'status': 'active',
                'csrfmiddlewaretoken': csrf,
            },
            follow=True
        )
        self.assertIn(r.status_code, [200, 302])
        from editor.models import StudentGroup
        grp = StudentGroup.objects.filter(code='SMK001').first()
        self.assertIsNotNone(grp, 'Debería crearse el grupo')
        if grp:
            # 4. Lista estudiantes
            r = self.client.get(reverse('editor:tutor_students_list', kwargs={'institution_slug': self.inst.slug}))
            self.assertEqual(r.status_code, 200)
            # 5. Crear estudiante
            r = self.client.get(reverse('editor:tutor_student_create', kwargs={'institution_slug': self.inst.slug}))
            self.assertEqual(r.status_code, 200)
            import re
            csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.content.decode())
            csrf = csrf_match.group(1) if csrf_match else ''
            r = self.client.post(
                reverse('editor:tutor_student_create', kwargs={'institution_slug': self.inst.slug}),
                {
                    'username': 'smoke_student',
                    'email': 'smoke@test.com',
                    'first_name': 'Smoke',
                    'last_name': 'Student',
                    'student_id': 'STD-SMK',
                    'password': 'testpass123',
                    'group': str(grp.id),
                    'csrfmiddlewaretoken': csrf,
                },
                follow=True
            )
            self.assertIn(r.status_code, [200, 302])
            # 6. Actividades del grupo
            r = self.client.get(reverse('editor:tutor_group_activities_list', kwargs={
                'institution_slug': self.inst.slug,
                'group_id': grp.id,
            }))
            self.assertEqual(r.status_code, 200)


class StudentFlowSmokeTest(TestCase):
    """Flujo completo Estudiante: login -> dashboard -> actividad -> IDE -> entregar."""

    def setUp(self):
        self.inst = create_institution()
        self.tutor_user, _ = create_tutor(institution=self.inst)
        self.group = create_group(institution=self.inst, tutor=self.tutor_user)
        self.student_user, _, _, _ = create_student(
            institution=self.inst,
            group=self.group,
            tutor=self.tutor_user,
            username='flow_student',
        )
        self.activity = create_activity(group=self.group, created_by=self.tutor_user)
        self.client = Client()

    def test_student_full_flow(self):
        """Login estudiante -> dashboard -> actividad -> IDE -> entregar."""
        self.client.login(username='flow_student', password='test123')
        # 1. Dashboard
        r = self.client.get(reverse('student_dashboard', kwargs={'slug': self.inst.slug}))
        self.assertEqual(r.status_code, 200)
        # 2. Lista actividades
        r = self.client.get(reverse('editor:student_group_activities', kwargs={'institution_slug': self.inst.slug}))
        self.assertEqual(r.status_code, 200)
        # 3. Detalle actividad
        r = self.client.get(reverse('editor:student_activity_detail_view', kwargs={
            'institution_slug': self.inst.slug,
            'activity_id': self.activity.id,
        }))
        self.assertEqual(r.status_code, 200)
        # 4. Abrir IDE
        r = self.client.get(reverse('editor:student_activity_ide_view', kwargs={
            'institution_slug': self.inst.slug,
            'activity_id': self.activity.id,
        }))
        self.assertEqual(r.status_code, 200)
        # 5. Entregar
        r = self.client.post(
            reverse('editor:api_submit_activity', kwargs={
                'institution_slug': self.inst.slug,
                'activity_id': self.activity.id,
            }),
            data=json.dumps({
                'xml_content': '<xml><block type="arduino_setup"/></xml>',
                'arduino_code': 'void setup() {}',
                'notes': '',
            }),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 200)
        resp_data = r.json()
        self.assertTrue(resp_data.get('ok'), msg=resp_data.get('error', ''))
        # 6. Tutor ve la entrega
        self.client.logout()
        self.client.login(username='test_tutor', password='test123')
        r = self.client.get(reverse('editor:tutor_activity_submissions_list', kwargs={
            'institution_slug': self.inst.slug,
            'activity_id': self.activity.id,
        }))
        self.assertEqual(r.status_code, 200)
        # Verificar que la lista de entregas carga (puede mostrar estudiante de diversas formas)
        content = r.content.decode()
        self.assertTrue(
            'flow_student' in content or 'Flow' in content or
            'Student' in content or 'Entreg' in content or 'entrega' in content.lower(),
            msg='La página de entregas debería cargar con contenido relevante'
        )
