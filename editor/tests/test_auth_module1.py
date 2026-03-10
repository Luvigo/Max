"""
MÓDULO 1: Tests de Auth + Roles
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from editor.models import Institution, Membership


class AuthenticationTests(TestCase):
    """Tests para el flujo de autenticación"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = Client()
        
        # Crear institución de prueba
        self.institution = Institution.objects.create(
            name="Test Institution",
            slug="test-inst",
            code="TEST001",
            status="active"
        )
        
        # Crear usuarios de prueba
        self.admin_user = User.objects.create_superuser(
            username="admin_test",
            email="admin@test.com",
            password="admin123"
        )
        
        self.tutor_user = User.objects.create_user(
            username="tutor_test",
            email="tutor@test.com",
            password="tutor123"
        )
        Membership.objects.create(
            user=self.tutor_user,
            institution=self.institution,
            role="tutor",
            is_active=True
        )
        
        self.student_user = User.objects.create_user(
            username="student_test",
            email="student@test.com",
            password="student123"
        )
        Membership.objects.create(
            user=self.student_user,
            institution=self.institution,
            role="student",
            is_active=True
        )
    
    def test_login_page_loads(self):
        """Test que la página de login carga correctamente"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iniciar Sesión')
    
    def test_login_invalid_credentials(self):
        """Test login con credenciales inválidas"""
        response = self.client.post(reverse('login'), {
            'username': 'invalid',
            'password': 'invalid'
        })
        self.assertEqual(response.status_code, 200)  # Muestra error, no redirect
        self.assertContains(response, 'nombre de usuario y clave correctos')
    
    def test_admin_redirects_to_django_admin(self):
        """Test que admin es redirigido a /admin/"""
        response = self.client.post(reverse('login'), {
            'username': 'admin_test',
            'password': 'admin123'
        })
        # Admin debe ser redirigido al login de admin
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/', response.url)
    
    def test_tutor_login_redirect(self):
        """Test que tutor es redirigido correctamente"""
        response = self.client.post(reverse('login'), {
            'username': 'tutor_test',
            'password': 'tutor123'
        }, follow=True)
        # Debe terminar en el dashboard del tutor
        self.assertEqual(response.status_code, 200)
    
    def test_student_login_redirect(self):
        """Test que estudiante es redirigido correctamente"""
        response = self.client.post(reverse('login'), {
            'username': 'student_test',
            'password': 'student123'
        }, follow=True)
        # Debe terminar en el dashboard del estudiante
        self.assertEqual(response.status_code, 200)
    
    def test_logout(self):
        """Test logout funciona correctamente"""
        self.client.login(username='tutor_test', password='tutor123')
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cerrado sesión')


class RoleAccessTests(TestCase):
    """Tests para verificación de acceso por roles"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        
        self.institution = Institution.objects.create(
            name="Test Institution",
            slug="test-inst",
            code="TEST001",
            status="active"
        )
        
        # Crear usuarios con diferentes roles
        self.tutor_user = User.objects.create_user(
            username="tutor_test",
            password="tutor123"
        )
        Membership.objects.create(
            user=self.tutor_user,
            institution=self.institution,
            role="tutor",
            is_active=True
        )
        
        self.student_user = User.objects.create_user(
            username="student_test",
            password="student123"
        )
        Membership.objects.create(
            user=self.student_user,
            institution=self.institution,
            role="student",
            is_active=True
        )
    
    def test_tutor_can_access_tutor_dashboard(self):
        """Test que tutor puede acceder a su dashboard"""
        self.client.login(username='tutor_test', password='tutor123')
        response = self.client.get(
            reverse('tutor_dashboard', kwargs={'slug': 'test-inst'})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_student_cannot_access_tutor_dashboard(self):
        """Test que estudiante NO puede acceder al dashboard de tutor"""
        self.client.login(username='student_test', password='student123')
        response = self.client.get(
            reverse('tutor_dashboard', kwargs={'slug': 'test-inst'})
        )
        # Debe ser redirigido (302) no 200
        self.assertIn(response.status_code, [302, 403])
    
    def test_student_can_access_student_dashboard(self):
        """Test que estudiante puede acceder a su dashboard"""
        self.client.login(username='student_test', password='student123')
        response = self.client.get(
            reverse('student_dashboard', kwargs={'slug': 'test-inst'})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_unauthenticated_redirects_to_login(self):
        """Test que usuarios no autenticados son redirigidos al login"""
        response = self.client.get(
            reverse('tutor_dashboard', kwargs={'slug': 'test-inst'})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class MembershipTests(TestCase):
    """Tests para el modelo Membership"""
    
    def setUp(self):
        self.institution = Institution.objects.create(
            name="Test Institution",
            slug="test-inst",
            code="TEST001"
        )
        self.user = User.objects.create_user(
            username="test_user",
            password="test123"
        )
    
    def test_membership_creation(self):
        """Test creación de membresía"""
        membership = Membership.objects.create(
            user=self.user,
            institution=self.institution,
            role="tutor"
        )
        self.assertEqual(membership.role, "tutor")
        self.assertTrue(membership.is_tutor_or_above)
        self.assertFalse(membership.is_student)
    
    def test_membership_roles(self):
        """Test propiedades de roles"""
        # Test admin
        membership = Membership.objects.create(
            user=self.user,
            institution=self.institution,
            role="admin"
        )
        self.assertTrue(membership.is_admin)
        self.assertTrue(membership.is_institution_admin)
        self.assertTrue(membership.is_tutor_or_above)
        
        # Cambiar a student
        membership.role = "student"
        membership.save()
        self.assertFalse(membership.is_admin)
        self.assertTrue(membership.is_student)
    
    def test_unique_membership_per_institution(self):
        """Test que un usuario solo puede tener una membresía por institución"""
        Membership.objects.create(
            user=self.user,
            institution=self.institution,
            role="tutor"
        )
        
        # Intentar crear otra membresía para el mismo usuario/institución
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Membership.objects.create(
                user=self.user,
                institution=self.institution,
                role="student"
            )
