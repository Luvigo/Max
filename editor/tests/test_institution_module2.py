"""
MÓDULO 2: Tests de Institución (entidad informativa)

Regla: NO hay vistas de admin para instituciones.
Solo vistas read-only para tutor y estudiante.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from editor.models import Institution, Membership, Course, Enrollment, TeachingAssignment


class InstitutionModelTests(TestCase):
    """Tests para el modelo Institution"""
    
    def setUp(self):
        """Configuración inicial"""
        self.institution = Institution.objects.create(
            name="Test Institution",
            slug="test-inst",
            code="TEST001",
            status="active",
            email="contact@test.edu",
            phone="+52 555 1234567",
            website="https://test.edu",
            address="Calle Test 123",
            city="Ciudad Test",
            state="Estado Test",
            country="México",
            postal_code="12345"
        )
        
        # Crear usuarios
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
    
    def test_institution_creation(self):
        """Test creación de institución con todos los campos"""
        self.assertEqual(self.institution.name, "Test Institution")
        self.assertEqual(self.institution.email, "contact@test.edu")
        self.assertEqual(self.institution.city, "Ciudad Test")
        self.assertTrue(self.institution.is_active)
    
    def test_institution_full_address(self):
        """Test método get_full_address"""
        address = self.institution.get_full_address()
        self.assertIn("Calle Test 123", address)
        self.assertIn("Ciudad Test", address)
        self.assertIn("México", address)
    
    def test_institution_tutors_count(self):
        """Test contador de tutores"""
        self.assertEqual(self.institution.get_tutors_count(), 1)
    
    def test_institution_students_count(self):
        """Test contador de estudiantes"""
        self.assertEqual(self.institution.get_students_count(), 1)
    
    def test_institution_get_tutors(self):
        """Test obtener lista de tutores"""
        tutors = self.institution.get_tutors()
        self.assertEqual(tutors.count(), 1)
        self.assertIn(self.tutor_user, tutors)
    
    def test_institution_get_students(self):
        """Test obtener lista de estudiantes"""
        students = self.institution.get_students()
        self.assertEqual(students.count(), 1)
        self.assertIn(self.student_user, students)
    
    def test_institution_slug_auto_generation(self):
        """Test que el slug se genera automáticamente"""
        inst = Institution.objects.create(
            name="Another Test Institution",
            code="TEST002"
        )
        self.assertIsNotNone(inst.slug)
        self.assertTrue(len(inst.slug) > 0)
    
    def test_institution_agent_token_auto_generation(self):
        """Test que el token de agent se genera automáticamente"""
        inst = Institution.objects.create(
            name="Token Test",
            code="TEST003"
        )
        self.assertIsNotNone(inst.agent_token)
        self.assertTrue(len(inst.agent_token) > 0)


class InstitutionReadOnlyViewsTests(TestCase):
    """Tests para las vistas read-only de institución"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        
        self.institution = Institution.objects.create(
            name="Test Institution",
            slug="test-inst",
            code="TEST001",
            status="active",
            email="contact@test.edu"
        )
        
        # Crear tutor
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
        
        # Crear estudiante
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
        
        # Crear usuario sin membresía
        self.no_member_user = User.objects.create_user(
            username="no_member",
            password="pass123"
        )
    
    def test_tutor_can_view_institution(self):
        """Test que tutor puede ver su institución"""
        self.client.login(username='tutor_test', password='tutor123')
        response = self.client.get(
            reverse('editor:tutor_my_institution', 
                    kwargs={'institution_slug': 'test-inst'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Institution')
    
    def test_student_can_view_institution(self):
        """Test que estudiante puede ver su institución"""
        self.client.login(username='student_test', password='student123')
        response = self.client.get(
            reverse('editor:student_my_institution', 
                    kwargs={'institution_slug': 'test-inst'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Institution')
    
    def test_unauthenticated_cannot_view(self):
        """Test que usuario no autenticado es redirigido"""
        response = self.client.get(
            reverse('editor:my_institution', 
                    kwargs={'institution_slug': 'test-inst'})
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_non_member_cannot_view(self):
        """Test que usuario sin membresía no puede ver institución ajena"""
        self.client.login(username='no_member', password='pass123')
        response = self.client.get(
            reverse('editor:my_institution', 
                    kwargs={'institution_slug': 'test-inst'})
        )
        # Debe ser redirigido
        self.assertIn(response.status_code, [302, 403])
    
    def test_view_shows_institution_info(self):
        """Test que la vista muestra información de la institución"""
        self.client.login(username='tutor_test', password='tutor123')
        response = self.client.get(
            reverse('editor:tutor_my_institution', 
                    kwargs={'institution_slug': 'test-inst'})
        )
        self.assertContains(response, 'TEST001')  # Código
        self.assertContains(response, 'contact@test.edu')  # Email


class InstitutionPermissionsTests(TestCase):
    """Tests de permisos para institución"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        
        self.institution1 = Institution.objects.create(
            name="Institution 1",
            slug="inst-1",
            code="INST001",
            status="active"
        )
        
        self.institution2 = Institution.objects.create(
            name="Institution 2",
            slug="inst-2",
            code="INST002",
            status="active"
        )
        
        # Usuario solo de institución 1
        self.user1 = User.objects.create_user(
            username="user1",
            password="pass123"
        )
        Membership.objects.create(
            user=self.user1,
            institution=self.institution1,
            role="student",
            is_active=True
        )
    
    def test_cross_institution_access_denied(self):
        """Test que usuario no puede ver institución a la que no pertenece"""
        self.client.login(username='user1', password='pass123')
        
        # Intentar acceder a institución 2 (no es miembro)
        response = self.client.get(
            reverse('editor:my_institution', 
                    kwargs={'institution_slug': 'inst-2'})
        )
        # Debe ser redirigido o denegado
        self.assertIn(response.status_code, [302, 403])
    
    def test_student_cannot_access_tutor_view(self):
        """Test que estudiante no puede acceder a vista de tutor"""
        self.client.login(username='user1', password='pass123')
        
        response = self.client.get(
            reverse('editor:tutor_my_institution', 
                    kwargs={'institution_slug': 'inst-1'})
        )
        # Debe ser redirigido (no tiene rol de tutor)
        self.assertIn(response.status_code, [302, 403])
    
    def test_inactive_institution_not_accessible(self):
        """Test que institución inactiva no es accesible"""
        self.institution1.status = 'inactive'
        self.institution1.save()
        
        self.client.login(username='user1', password='pass123')
        response = self.client.get(
            reverse('editor:my_institution', 
                    kwargs={'institution_slug': 'inst-1'})
        )
        # Debe dar 404 o redirect
        self.assertIn(response.status_code, [302, 404])


class InstitutionAdminTests(TestCase):
    """Tests para verificar que el admin funciona correctamente"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        
        # Crear superuser
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="admin123"
        )
        
        self.institution = Institution.objects.create(
            name="Test Institution",
            slug="test-inst",
            code="TEST001",
            status="active"
        )
    
    def test_admin_can_access_institution_list(self):
        """Test que admin puede ver lista de instituciones en Django Admin"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/admin/editor/institution/')
        self.assertEqual(response.status_code, 200)
    
    def test_admin_can_access_institution_change(self):
        """Test que admin puede editar institución en Django Admin"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(f'/admin/editor/institution/{self.institution.id}/change/')
        self.assertEqual(response.status_code, 200)
    
    def test_normal_user_cannot_access_admin(self):
        """Test que usuario normal no puede acceder al admin"""
        normal_user = User.objects.create_user(
            username="normal",
            password="normal123"
        )
        self.client.login(username='normal', password='normal123')
        response = self.client.get('/admin/editor/institution/')
        # Debe ser redirigido al login de admin
        self.assertIn(response.status_code, [302, 403])
