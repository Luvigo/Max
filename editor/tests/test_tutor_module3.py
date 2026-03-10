"""
MÓDULO 3: Tests de Gestión de Tutores

Tests para:
- TutorProfile model
- Django Admin para tutores
- Vista read-only de perfil
- Bloqueo de tutores inactivos
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from editor.models import Institution, Membership, TutorProfile, Course, TeachingAssignment


class TutorProfileModelTest(TestCase):
    """Tests para el modelo TutorProfile"""
    
    def setUp(self):
        # Crear institución
        self.institution = Institution.objects.create(
            name='Test Institution',
            slug='test-inst',
            status='active'
        )
        
        # Crear usuario tutor
        self.tutor_user = User.objects.create_user(
            username='test_tutor',
            email='tutor@test.com',
            password='test123',
            first_name='Test',
            last_name='Tutor'
        )
        
        # Crear TutorProfile
        self.tutor_profile = TutorProfile.objects.create(
            user=self.tutor_user,
            institution=self.institution,
            title='Ing.',
            specialization='Programación',
            status='active'
        )
        
        # Crear Membership
        self.membership = Membership.objects.create(
            user=self.tutor_user,
            institution=self.institution,
            role='tutor',
            is_active=True
        )
    
    def test_tutor_profile_creation(self):
        """TutorProfile se crea correctamente"""
        self.assertEqual(self.tutor_profile.user, self.tutor_user)
        self.assertEqual(self.tutor_profile.institution, self.institution)
        self.assertEqual(self.tutor_profile.status, 'active')
    
    def test_full_name_with_title(self):
        """full_name incluye el título"""
        self.assertEqual(self.tutor_profile.full_name, 'Ing. Test Tutor')
    
    def test_full_name_without_title(self):
        """full_name funciona sin título"""
        self.tutor_profile.title = ''
        self.tutor_profile.save()
        self.assertEqual(self.tutor_profile.full_name, 'Test Tutor')
    
    def test_is_active_property(self):
        """is_active refleja el status"""
        self.assertTrue(self.tutor_profile.is_active)
        
        self.tutor_profile.status = 'inactive'
        self.tutor_profile.save()
        self.assertFalse(self.tutor_profile.is_active)
    
    def test_can_login_active(self):
        """can_login es True si está activo"""
        self.assertTrue(self.tutor_profile.can_login())
    
    def test_can_login_inactive(self):
        """can_login es False si está inactivo"""
        self.tutor_profile.status = 'inactive'
        self.tutor_profile.save()
        self.assertFalse(self.tutor_profile.can_login())
    
    def test_can_login_user_inactive(self):
        """can_login es False si el user está inactivo"""
        self.tutor_user.is_active = False
        self.tutor_user.save()
        self.assertFalse(self.tutor_profile.can_login())
    
    def test_deactivate(self):
        """deactivate cambia status y membership"""
        self.tutor_profile.deactivate()
        
        self.tutor_profile.refresh_from_db()
        self.membership.refresh_from_db()
        
        self.assertEqual(self.tutor_profile.status, 'inactive')
        self.assertFalse(self.membership.is_active)
    
    def test_activate(self):
        """activate cambia status y membership"""
        self.tutor_profile.status = 'inactive'
        self.tutor_profile.save()
        self.membership.is_active = False
        self.membership.save()
        
        self.tutor_profile.activate()
        
        self.tutor_profile.refresh_from_db()
        self.membership.refresh_from_db()
        
        self.assertEqual(self.tutor_profile.status, 'active')
        self.assertTrue(self.membership.is_active)
    
    def test_get_courses_count(self):
        """get_courses_count cuenta cursos asignados"""
        # Sin cursos
        self.assertEqual(self.tutor_profile.get_courses_count(), 0)
        
        # Crear curso y asignación
        course = Course.objects.create(
            institution=self.institution,
            name='Test Course',
            code='TC001',
            academic_year='2026'
        )
        TeachingAssignment.objects.create(
            course=course,
            tutor=self.tutor_user,
            status='active'
        )
        
        self.assertEqual(self.tutor_profile.get_courses_count(), 1)


class TutorProfileViewTest(TestCase):
    """Tests para la vista de perfil del tutor"""
    
    def setUp(self):
        self.client = Client()
        
        # Crear institución
        self.institution = Institution.objects.create(
            name='Test Institution',
            slug='test-inst',
            status='active'
        )
        
        # Crear tutor
        self.tutor_user = User.objects.create_user(
            username='test_tutor',
            email='tutor@test.com',
            password='test123',
            first_name='Test',
            last_name='Tutor'
        )
        
        self.tutor_profile = TutorProfile.objects.create(
            user=self.tutor_user,
            institution=self.institution,
            status='active'
        )
        
        self.membership = Membership.objects.create(
            user=self.tutor_user,
            institution=self.institution,
            role='tutor',
            is_active=True
        )
        
        # Crear estudiante (para probar acceso denegado)
        self.student_user = User.objects.create_user(
            username='test_student',
            email='student@test.com',
            password='test123'
        )
        
        Membership.objects.create(
            user=self.student_user,
            institution=self.institution,
            role='student',
            is_active=True
        )
    
    def test_tutor_can_view_profile(self):
        """Tutor puede ver su perfil"""
        self.client.login(username='test_tutor', password='test123')
        response = self.client.get(
            reverse('editor:tutor_profile', kwargs={'institution_slug': 'test-inst'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mi Perfil de Tutor')
    
    def test_student_cannot_view_tutor_profile(self):
        """Estudiante no puede ver perfil de tutor"""
        self.client.login(username='test_student', password='test123')
        response = self.client.get(
            reverse('editor:tutor_profile', kwargs={'institution_slug': 'test-inst'})
        )
        # Debe redirigir a acceso denegado o dashboard
        self.assertIn(response.status_code, [302, 403])
    
    def test_anonymous_cannot_view_profile(self):
        """Usuario anónimo no puede ver perfil"""
        response = self.client.get(
            reverse('editor:tutor_profile', kwargs={'institution_slug': 'test-inst'})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class TutorInactiveBlockTest(TestCase):
    """Tests para bloqueo de tutores inactivos"""
    
    def setUp(self):
        self.client = Client()
        
        self.institution = Institution.objects.create(
            name='Test Institution',
            slug='test-inst',
            status='active'
        )
        
        self.tutor_user = User.objects.create_user(
            username='test_tutor',
            email='tutor@test.com',
            password='test123'
        )
        
        self.tutor_profile = TutorProfile.objects.create(
            user=self.tutor_user,
            institution=self.institution,
            status='active'
        )
        
        self.membership = Membership.objects.create(
            user=self.tutor_user,
            institution=self.institution,
            role='tutor',
            is_active=True
        )
    
    def test_active_tutor_can_access(self):
        """Tutor activo puede acceder a vistas de tutor"""
        self.client.login(username='test_tutor', password='test123')
        response = self.client.get(
            reverse('editor:tutor_profile', kwargs={'institution_slug': 'test-inst'})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_inactive_tutor_blocked(self):
        """Tutor inactivo es bloqueado"""
        self.tutor_profile.status = 'inactive'
        self.tutor_profile.save()
        
        self.client.login(username='test_tutor', password='test123')
        response = self.client.get(
            reverse('editor:tutor_profile', kwargs={'institution_slug': 'test-inst'})
        )
        # Debe redirigir
        self.assertEqual(response.status_code, 302)
    
    def test_suspended_tutor_blocked(self):
        """Tutor suspendido es bloqueado"""
        self.tutor_profile.status = 'suspended'
        self.tutor_profile.save()
        
        self.client.login(username='test_tutor', password='test123')
        response = self.client.get(
            reverse('editor:tutor_profile', kwargs={'institution_slug': 'test-inst'})
        )
        self.assertEqual(response.status_code, 302)


class TutorStatusAPITest(TestCase):
    """Tests para API de estado del tutor"""
    
    def setUp(self):
        self.client = Client()
        
        self.institution = Institution.objects.create(
            name='Test Institution',
            slug='test-inst',
            status='active'
        )
        
        self.tutor_user = User.objects.create_user(
            username='test_tutor',
            email='tutor@test.com',
            password='test123'
        )
        
        self.tutor_profile = TutorProfile.objects.create(
            user=self.tutor_user,
            institution=self.institution,
            status='active'
        )
        
        self.membership = Membership.objects.create(
            user=self.tutor_user,
            institution=self.institution,
            role='tutor',
            is_active=True
        )
    
    def test_check_status_active(self):
        """API retorna activo para tutor activo"""
        self.client.login(username='test_tutor', password='test123')
        response = self.client.get(
            reverse('editor:api_tutor_status', kwargs={'institution_slug': 'test-inst'})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertTrue(data['active'])
    
    def test_check_status_inactive(self):
        """API retorna inactivo para tutor inactivo"""
        self.tutor_profile.status = 'inactive'
        self.tutor_profile.save()
        
        self.client.login(username='test_tutor', password='test123')
        response = self.client.get(
            reverse('editor:api_tutor_status', kwargs={'institution_slug': 'test-inst'})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['ok'])
        self.assertFalse(data['active'])
