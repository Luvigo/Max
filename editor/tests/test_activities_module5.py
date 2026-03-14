"""
Tests para MÓDULO 5: Actividades y Entregas por Grupo

Tests de:
- Creación de actividades por tutor
- Entregas de estudiantes
- Permisos y acceso
- APIs de submit y autosave
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json

from editor.models import (
    Institution, Membership, StudentGroup, Student, Activity, Submission
)


class ActivityModelTest(TestCase):
    """Tests para el modelo Activity"""
    
    def setUp(self):
        # Crear institución
        self.institution = Institution.objects.create(
            name='Test Institution',
            slug='test-institution',
            status='active'
        )
        
        # Crear tutor
        self.tutor = User.objects.create_user(
            username='tutor_test',
            email='tutor@test.com',
            password='test123'
        )
        Membership.objects.create(
            user=self.tutor,
            institution=self.institution,
            role='tutor',
            is_active=True
        )
        
        # Crear grupo
        self.group = StudentGroup.objects.create(
            institution=self.institution,
            tutor=self.tutor,
            name='Grupo Test',
            code='GRP001',
            status='active'
        )
        
        # Crear estudiante
        self.student_user = User.objects.create_user(
            username='student_test',
            email='student@test.com',
            password='test123'
        )
        Membership.objects.create(
            user=self.student_user,
            institution=self.institution,
            role='student',
            is_active=True
        )
        self.student = Student.objects.create(
            user=self.student_user,
            student_id='STD001',
            institution=self.institution,
            group=self.group
        )
    
    def test_create_activity(self):
        """Test crear actividad"""
        activity = Activity.objects.create(
            group=self.group,
            created_by=self.tutor,
            title='Test Activity',
            instructions='Test instructions',
            status='draft'
        )
        
        self.assertEqual(activity.group, self.group)
        self.assertEqual(activity.status, 'draft')
        self.assertEqual(activity.institution, self.institution)
        self.assertEqual(activity.tutor, self.tutor)
    
    def test_activity_can_submit_not_published(self):
        """Test que no se puede entregar actividad no publicada"""
        activity = Activity.objects.create(
            group=self.group,
            created_by=self.tutor,
            title='Test Activity',
            instructions='Test instructions',
            status='draft'
        )
        
        can_submit, reason = activity.can_submit(self.student_user)
        self.assertFalse(can_submit)
        self.assertIn('no está publicada', reason.lower())
    
    def test_activity_can_submit_wrong_group(self):
        """Test que estudiante de otro grupo no puede entregar"""
        # Crear otro grupo y estudiante
        other_group = StudentGroup.objects.create(
            institution=self.institution,
            tutor=self.tutor,
            name='Otro Grupo',
            code='GRP002',
            status='active'
        )
        other_student_user = User.objects.create_user(
            username='other_student',
            email='other@test.com',
            password='test123'
        )
        Student.objects.create(
            user=other_student_user,
            student_id='STD002',
            institution=self.institution,
            group=other_group
        )
        
        activity = Activity.objects.create(
            group=self.group,  # Actividad para group original
            created_by=self.tutor,
            title='Test Activity',
            instructions='Test instructions',
            status='published',
            published_at=timezone.now()
        )
        
        can_submit, reason = activity.can_submit(other_student_user)
        self.assertFalse(can_submit)
        self.assertIn('no perteneces', reason.lower())
    
    def test_activity_can_submit_deadline_passed(self):
        """Test que no se puede entregar después del deadline"""
        activity = Activity.objects.create(
            group=self.group,
            created_by=self.tutor,
            title='Test Activity',
            instructions='Test instructions',
            status='published',
            published_at=timezone.now(),
            deadline=timezone.now() - timedelta(days=1),  # Ya pasó
            allow_late_submit=False
        )
        
        can_submit, reason = activity.can_submit(self.student_user)
        self.assertFalse(can_submit)
        self.assertIn('fecha límite', reason.lower())
    
    def test_activity_can_submit_success(self):
        """Test que estudiante puede entregar normalmente"""
        activity = Activity.objects.create(
            group=self.group,
            created_by=self.tutor,
            title='Test Activity',
            instructions='Test instructions',
            status='published',
            published_at=timezone.now(),
            deadline=timezone.now() + timedelta(days=7)  # Futuro
        )
        
        can_submit, reason = activity.can_submit(self.student_user)
        self.assertTrue(can_submit)
        self.assertEqual(reason, 'OK')


class SubmissionModelTest(TestCase):
    """Tests para el modelo Submission"""
    
    def setUp(self):
        self.institution = Institution.objects.create(
            name='Test Institution',
            slug='test-institution',
            status='active'
        )
        self.tutor = User.objects.create_user(
            username='tutor_test',
            email='tutor@test.com',
            password='test123'
        )
        Membership.objects.create(
            user=self.tutor,
            institution=self.institution,
            role='tutor'
        )
        self.group = StudentGroup.objects.create(
            institution=self.institution,
            tutor=self.tutor,
            name='Grupo Test',
            code='GRP001',
            status='active'
        )
        self.student_user = User.objects.create_user(
            username='student_test',
            email='student@test.com',
            password='test123'
        )
        Membership.objects.create(
            user=self.student_user,
            institution=self.institution,
            role='student'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            student_id='STD001',
            institution=self.institution,
            group=self.group
        )
        self.activity = Activity.objects.create(
            group=self.group,
            created_by=self.tutor,
            title='Test Activity',
            instructions='Test instructions',
            status='published',
            published_at=timezone.now()
        )
    
    def test_create_submission(self):
        """Test crear entrega"""
        submission = Submission.objects.create(
            activity=self.activity,
            student=self.student_user,
            status='in_progress',
            attempt=1
        )
        
        self.assertEqual(submission.activity, self.activity)
        self.assertEqual(submission.student, self.student_user)
        self.assertEqual(submission.status, 'in_progress')
    
    def test_submit_method(self):
        """Test método submit()"""
        submission = Submission.objects.create(
            activity=self.activity,
            student=self.student_user,
            status='in_progress',
            attempt=1
        )
        
        xml_content = '<xml>test</xml>'
        arduino_code = 'void setup() {}'
        notes = 'Test notes'
        
        submission.submit(xml_content, arduino_code, notes)
        
        self.assertEqual(submission.status, 'submitted')
        self.assertEqual(submission.xml_content, xml_content)
        self.assertEqual(submission.arduino_code, arduino_code)
        self.assertEqual(submission.notes, notes)
        self.assertTrue(submission.is_read_only)
        self.assertIsNotNone(submission.submitted_at)
    
    def test_grade_method(self):
        """Test método grade()"""
        submission = Submission.objects.create(
            activity=self.activity,
            student=self.student_user,
            status='submitted',
            attempt=1
        )
        
        submission.grade(85.5, self.tutor, 'Buen trabajo')
        
        self.assertEqual(submission.status, 'graded')
        self.assertEqual(submission.score, 85.5)
        self.assertEqual(submission.graded_by, self.tutor)
        self.assertIsNotNone(submission.graded_at)


class ActivityViewsTest(TestCase):
    """Tests para las vistas de actividades"""
    
    def setUp(self):
        self.client = Client()
        
        self.institution = Institution.objects.create(
            name='Test Institution',
            slug='test-institution',
            status='active'
        )
        
        # Tutor
        self.tutor = User.objects.create_user(
            username='tutor_test',
            email='tutor@test.com',
            password='test123'
        )
        Membership.objects.create(
            user=self.tutor,
            institution=self.institution,
            role='tutor',
            is_active=True
        )
        
        # Grupo
        self.group = StudentGroup.objects.create(
            institution=self.institution,
            tutor=self.tutor,
            name='Grupo Test',
            code='GRP001',
            status='active'
        )
        
        # Estudiante
        self.student_user = User.objects.create_user(
            username='student_test',
            email='student@test.com',
            password='test123'
        )
        Membership.objects.create(
            user=self.student_user,
            institution=self.institution,
            role='student',
            is_active=True
        )
        self.student = Student.objects.create(
            user=self.student_user,
            student_id='STD001',
            institution=self.institution,
            group=self.group,
            is_active=True
        )
        
        # Actividad
        self.activity = Activity.objects.create(
            group=self.group,
            created_by=self.tutor,
            title='Test Activity',
            instructions='Test instructions',
            status='published',
            published_at=timezone.now(),
            max_score=100
        )
    
    def test_tutor_activities_list(self):
        """Test lista de actividades de tutor"""
        self.client.login(username='tutor_test', password='test123')
        
        url = f'/i/{self.institution.slug}/tutor/groups/{self.group.id}/activities/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Activity')
    
    def test_student_activities_list(self):
        """Test lista de actividades de estudiante"""
        self.client.login(username='student_test', password='test123')
        
        url = f'/i/{self.institution.slug}/student/activities/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Activity')
    
    def test_student_activity_ide(self):
        """Test IDE de actividad de estudiante"""
        self.client.login(username='student_test', password='test123')
        
        url = f'/i/{self.institution.slug}/student/activities/{self.activity.id}/ide/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Activity')


class SubmitAPITest(TestCase):
    """Tests para las APIs de submit"""
    
    def setUp(self):
        self.client = Client()
        
        self.institution = Institution.objects.create(
            name='Test Institution',
            slug='test-institution',
            status='active'
        )
        
        self.tutor = User.objects.create_user(
            username='tutor_test',
            email='tutor@test.com',
            password='test123'
        )
        Membership.objects.create(
            user=self.tutor,
            institution=self.institution,
            role='tutor'
        )
        
        self.group = StudentGroup.objects.create(
            institution=self.institution,
            tutor=self.tutor,
            name='Grupo Test',
            code='GRP001',
            status='active'
        )
        
        self.student_user = User.objects.create_user(
            username='student_test',
            email='student@test.com',
            password='test123'
        )
        Membership.objects.create(
            user=self.student_user,
            institution=self.institution,
            role='student',
            is_active=True
        )
        self.student = Student.objects.create(
            user=self.student_user,
            student_id='STD001',
            institution=self.institution,
            group=self.group,
            is_active=True
        )
        
        self.activity = Activity.objects.create(
            group=self.group,
            created_by=self.tutor,
            title='Test Activity',
            instructions='Test instructions',
            status='published',
            published_at=timezone.now(),
            max_score=100
        )
    
    def test_submit_activity_success(self):
        """Test entrega exitosa de actividad"""
        self.client.login(username='student_test', password='test123')
        
        url = f'/i/{self.institution.slug}/api/activity/{self.activity.id}/submit/'
        data = {
            'xml_content': '<xml>test</xml>',
            'arduino_code': 'void setup() {}',
            'notes': 'Test notes'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result['ok'])
        self.assertIn('submission_id', result)
        
        # Verificar submission creada
        submission = Submission.objects.get(
            activity=self.activity,
            student=self.student_user
        )
        self.assertEqual(submission.status, 'submitted')
        self.assertTrue(submission.is_read_only)
    
    def test_submit_activity_wrong_group(self):
        """Test que estudiante de otro grupo no puede entregar"""
        # Crear otro estudiante sin grupo
        other_user = User.objects.create_user(
            username='other_student',
            email='other@test.com',
            password='test123'
        )
        Membership.objects.create(
            user=other_user,
            institution=self.institution,
            role='student',
            is_active=True
        )
        Student.objects.create(
            user=other_user,
            student_id='STD002',
            institution=self.institution,
            group=None,  # Sin grupo
            is_active=True
        )
        
        self.client.login(username='other_student', password='test123')
        
        url = f'/i/{self.institution.slug}/api/activity/{self.activity.id}/submit/'
        data = {
            'xml_content': '<xml>test</xml>',
            'arduino_code': 'void setup() {}',
            'notes': 'Test notes'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertFalse(result['ok'])
    
    def test_save_progress(self):
        """Test guardar progreso (autosave)"""
        self.client.login(username='student_test', password='test123')
        
        url = f'/i/{self.institution.slug}/api/activity/{self.activity.id}/save/'
        data = {
            'xml_content': '<xml>in progress</xml>',
            'arduino_code': 'void setup() { // in progress }'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result['ok'])
        
        # Verificar submission creada en in_progress
        submission = Submission.objects.get(
            activity=self.activity,
            student=self.student_user
        )
        self.assertEqual(submission.status, 'in_progress')
        self.assertFalse(submission.is_read_only)
