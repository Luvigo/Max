"""
Tests para Módulo 1: Multi-tenant + RBAC + Dashboards
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Institution, Membership, Course, Student, Project, UserRoleHelper


class InstitutionModelTest(TestCase):
    """Tests para el modelo Institution"""
    
    def test_create_institution_generates_slug(self):
        """Verifica que se genere slug automáticamente"""
        inst = Institution.objects.create(
            name="Mi Colegio Test",
            code="MCT001"
        )
        self.assertEqual(inst.slug, "mi-colegio-test")
    
    def test_unique_slug_generation(self):
        """Verifica que los slugs sean únicos"""
        inst1 = Institution.objects.create(name="Test", code="T001")
        inst2 = Institution.objects.create(name="Test", code="T002")
        self.assertNotEqual(inst1.slug, inst2.slug)
    
    def test_status_syncs_with_is_active(self):
        """Verifica que is_active se sincroniza con status"""
        inst = Institution.objects.create(name="Test", code="T001", status='active')
        self.assertTrue(inst.is_active)
        
        inst.status = 'inactive'
        inst.save()
        self.assertFalse(inst.is_active)


class MembershipModelTest(TestCase):
    """Tests para el modelo Membership"""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'password')
        self.institution = Institution.objects.create(name="Test Inst", code="TI001")
    
    def test_create_membership(self):
        """Verifica creación de membresía"""
        membership = Membership.objects.create(
            user=self.user,
            institution=self.institution,
            role='student'
        )
        self.assertEqual(membership.role, 'student')
        self.assertTrue(membership.is_active)
    
    def test_role_properties(self):
        """Verifica propiedades de rol"""
        # Admin
        m_admin = Membership.objects.create(
            user=self.user,
            institution=self.institution,
            role='admin'
        )
        self.assertTrue(m_admin.is_admin)
        self.assertTrue(m_admin.is_institution_admin)
        self.assertTrue(m_admin.is_tutor_or_above)
        
    def test_unique_user_institution(self):
        """Verifica que user+institution sea único"""
        Membership.objects.create(
            user=self.user,
            institution=self.institution,
            role='student'
        )
        with self.assertRaises(Exception):
            Membership.objects.create(
                user=self.user,
                institution=self.institution,
                role='tutor'
            )


class UserRoleHelperTest(TestCase):
    """Tests para UserRoleHelper"""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'password')
        self.superuser = User.objects.create_superuser('admin', 'admin@test.com', 'password')
        self.institution = Institution.objects.create(name="Test Inst", code="TI001")
    
    def test_superuser_is_admin(self):
        """Superuser siempre tiene rol admin"""
        role = UserRoleHelper.get_user_role(self.superuser)
        self.assertEqual(role, 'admin')
    
    def test_get_user_role_with_institution(self):
        """Obtener rol en institución específica"""
        Membership.objects.create(
            user=self.user,
            institution=self.institution,
            role='tutor'
        )
        role = UserRoleHelper.get_user_role(self.user, self.institution)
        self.assertEqual(role, 'tutor')
    
    def test_get_user_institutions(self):
        """Obtener instituciones del usuario"""
        Membership.objects.create(
            user=self.user,
            institution=self.institution,
            role='student'
        )
        institutions = UserRoleHelper.get_user_institutions(self.user)
        self.assertEqual(institutions.count(), 1)
        self.assertEqual(institutions.first(), self.institution)
    
    def test_superuser_sees_all_institutions(self):
        """Superuser ve todas las instituciones"""
        Institution.objects.create(name="Inst 2", code="I002")
        institutions = UserRoleHelper.get_user_institutions(self.superuser)
        self.assertEqual(institutions.count(), 2)
    
    def test_user_has_role(self):
        """Verificar si usuario tiene rol"""
        Membership.objects.create(
            user=self.user,
            institution=self.institution,
            role='tutor'
        )
        self.assertTrue(UserRoleHelper.user_has_role(self.user, ['tutor', 'admin']))
        self.assertFalse(UserRoleHelper.user_has_role(self.user, ['admin']))


class TenantMiddlewareTest(TestCase):
    """Tests para TenantMiddleware"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('testuser', 'test@test.com', 'password')
        self.institution = Institution.objects.create(
            name="Test Inst",
            code="TI001",
            slug="test-inst"
        )
        Membership.objects.create(
            user=self.user,
            institution=self.institution,
            role='student'
        )
    
    def test_tenant_resolution_from_url(self):
        """Verifica que el tenant se resuelve desde la URL"""
        self.client.login(username='testuser', password='password')
        response = self.client.get(f'/i/{self.institution.slug}/dashboard/student/')
        # Puede redirigir o mostrar, pero no debe dar error 500
        self.assertIn(response.status_code, [200, 302])


class DashboardAccessTest(TestCase):
    """Tests de acceso a dashboards por rol"""
    
    def setUp(self):
        self.client = Client()
        self.institution = Institution.objects.create(
            name="Test Inst",
            code="TI001",
            slug="test-inst"
        )
        
        # Crear usuarios con diferentes roles
        self.admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'adminpass')
        
        self.inst_admin = User.objects.create_user('instadmin', 'inst@test.com', 'instpass')
        Membership.objects.create(user=self.inst_admin, institution=self.institution, role='institution')
        
        self.tutor = User.objects.create_user('tutor', 'tutor@test.com', 'tutorpass')
        Membership.objects.create(user=self.tutor, institution=self.institution, role='tutor')
        
        self.student = User.objects.create_user('student', 'student@test.com', 'studentpass')
        Membership.objects.create(user=self.student, institution=self.institution, role='student')
    
    def test_admin_can_access_admin_dashboard(self):
        """Admin puede acceder al dashboard admin"""
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_student_cannot_access_admin_dashboard(self):
        """Estudiante no puede acceder al dashboard admin"""
        self.client.login(username='student', password='studentpass')
        response = self.client.get(reverse('admin_dashboard'))
        # Debe redirigir al dashboard correcto
        self.assertEqual(response.status_code, 302)
    
    def test_tutor_can_access_tutor_dashboard(self):
        """Tutor puede acceder a su dashboard"""
        self.client.login(username='tutor', password='tutorpass')
        response = self.client.get(
            reverse('tutor_dashboard', kwargs={'slug': self.institution.slug})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_student_can_access_student_dashboard(self):
        """Estudiante puede acceder a su dashboard"""
        self.client.login(username='student', password='studentpass')
        response = self.client.get(
            reverse('student_dashboard', kwargs={'slug': self.institution.slug})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_unauthenticated_redirects_to_login(self):
        """Usuario no autenticado redirige a login"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class TenantScopingTest(TestCase):
    """Tests de tenant scoping (cross-tenant protection)"""
    
    def setUp(self):
        self.client = Client()
        
        # Crear dos instituciones
        self.inst1 = Institution.objects.create(name="Inst 1", code="I001", slug="inst-1")
        self.inst2 = Institution.objects.create(name="Inst 2", code="I002", slug="inst-2")
        
        # Usuario solo en inst1
        self.user1 = User.objects.create_user('user1', 'user1@test.com', 'pass1')
        Membership.objects.create(user=self.user1, institution=self.inst1, role='institution')
        
        # Usuario solo en inst2
        self.user2 = User.objects.create_user('user2', 'user2@test.com', 'pass2')
        Membership.objects.create(user=self.user2, institution=self.inst2, role='institution')
    
    def test_user_cannot_access_other_institution_dashboard(self):
        """Usuario no puede acceder a dashboard de otra institución"""
        self.client.login(username='user1', password='pass1')
        
        # Intentar acceder a inst2
        response = self.client.get(
            reverse('institution_dashboard', kwargs={'slug': self.inst2.slug})
        )
        # Debe redirigir (sin acceso)
        self.assertEqual(response.status_code, 302)
    
    def test_user_can_access_own_institution_dashboard(self):
        """Usuario puede acceder a dashboard de su institución"""
        self.client.login(username='user1', password='pass1')
        
        response = self.client.get(
            reverse('institution_dashboard', kwargs={'slug': self.inst1.slug})
        )
        self.assertEqual(response.status_code, 200)


class DashboardRedirectTest(TestCase):
    """Tests de redirección automática de dashboard"""
    
    def setUp(self):
        self.client = Client()
        self.institution = Institution.objects.create(name="Test", code="T001", slug="test")
    
    def test_single_institution_auto_redirect(self):
        """Usuario con una sola institución redirige automáticamente"""
        user = User.objects.create_user('single', 'single@test.com', 'pass')
        Membership.objects.create(user=user, institution=self.institution, role='student')
        
        self.client.login(username='single', password='pass')
        response = self.client.get(reverse('dashboard'))
        
        # Debe redirigir al dashboard de estudiante
        self.assertEqual(response.status_code, 302)
    
    def test_multiple_institutions_shows_selector(self):
        """Usuario con múltiples instituciones ve selector"""
        inst2 = Institution.objects.create(name="Test 2", code="T002", slug="test-2")
        
        user = User.objects.create_user('multi', 'multi@test.com', 'pass')
        Membership.objects.create(user=user, institution=self.institution, role='student')
        Membership.objects.create(user=user, institution=inst2, role='tutor')
        
        self.client.login(username='multi', password='pass')
        response = self.client.get(reverse('dashboard'))
        
        # Debe redirigir al selector de institución
        self.assertEqual(response.status_code, 302)
        self.assertIn('select-institution', response.url)
