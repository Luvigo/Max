"""
TESTS DE LIMPIEZA ARQUITECTÓNICA

Garantía de No-Regresión:
- NO debe existir dashboard de admin en templates
- NO debe existir dashboard de institución funcional
- El admin SOLO opera desde /admin/
- Solo Tutor y Estudiante tienen dashboards en la plataforma

Estos tests fallarán si se intenta re-introducir roles/vistas deprecadas.
"""
from django.test import TestCase, Client
from django.urls import reverse, resolve, Resolver404
from django.contrib.auth import get_user_model
from editor.models import Institution, Membership

User = get_user_model()


class ArchitectureCleanupTest(TestCase):
    """
    Tests que validan la limpieza arquitectónica.
    """
    
    @classmethod
    def setUpTestData(cls):
        # Crear institución de prueba
        cls.institution = Institution.objects.create(
            name='Test Institution',
            code='TEST-001',
            slug='test-institution',
            status='active'
        )
        
        # Crear usuarios con diferentes roles
        cls.admin_user = User.objects.create_superuser(
            username='test_admin',
            email='admin@test.com',
            password='admin123'
        )
        
        cls.tutor_user = User.objects.create_user(
            username='test_tutor',
            email='tutor@test.com',
            password='tutor123'
        )
        Membership.objects.create(
            user=cls.tutor_user,
            institution=cls.institution,
            role='tutor',
            is_active=True
        )
        
        cls.student_user = User.objects.create_user(
            username='test_student',
            email='student@test.com',
            password='student123'
        )
        Membership.objects.create(
            user=cls.student_user,
            institution=cls.institution,
            role='student',
            is_active=True
        )
        
        # Usuario con rol deprecado "institution"
        cls.institution_user = User.objects.create_user(
            username='test_institution',
            email='inst@test.com',
            password='inst123'
        )
        Membership.objects.create(
            user=cls.institution_user,
            institution=cls.institution,
            role='institution',  # ROL DEPRECADO
            is_active=True
        )
    
    def setUp(self):
        self.client = Client()
    
    # ============================================
    # TESTS: ADMIN SOLO USA DJANGO ADMIN
    # ============================================
    
    def test_admin_redirects_to_django_admin(self):
        """El admin debe ser redirigido a /admin/"""
        self.client.login(username='test_admin', password='admin123')
        response = self.client.get('/dashboard/')
        
        # Debe redirigir a /admin/
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/', response.url)
    
    def test_admin_dashboard_route_redirects(self):
        """La ruta /dashboard/admin/ debe redirigir a /admin/"""
        self.client.login(username='test_admin', password='admin123')
        response = self.client.get('/dashboard/admin/')
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/', response.url)
    
    def test_admin_panel_routes_redirect(self):
        """Las rutas /admin-panel/* deben redirigir a /admin/"""
        self.client.login(username='test_admin', password='admin123')
        
        routes_to_test = [
            '/admin-panel/',
            '/admin-panel/agents/',
            '/admin-panel/errors/',
        ]
        
        for route in routes_to_test:
            response = self.client.get(route)
            self.assertEqual(
                response.status_code, 302,
                f"Route {route} should redirect"
            )
            self.assertIn('/admin/', response.url, f"Route {route} should redirect to /admin/")
    
    # ============================================
    # TESTS: INSTITUCIÓN NO TIENE DASHBOARD
    # ============================================
    
    def test_institution_role_is_deprecated(self):
        """Usuario con rol 'institution' no debe poder acceder a dashboards"""
        self.client.login(username='test_institution', password='inst123')
        response = self.client.get('/dashboard/')
        
        # Debe mostrar mensaje de deprecación o redirigir a login
        # Verificar que no llega a un dashboard funcional
        self.assertIn(response.status_code, [200, 302])
        
        if response.status_code == 200:
            # Si muestra página, debe ser de error/deprecación
            content = response.content.decode('utf-8').lower()
            self.assertTrue(
                'deprecado' in content or 'deprec' in content or 'no válido' in content,
                "Usuario con rol institution debe ver mensaje de deprecación"
            )
    
    def test_institution_dashboard_redirects_or_shows_message(self):
        """El dashboard de institución debe redirigir o mostrar mensaje"""
        self.client.login(username='test_institution', password='inst123')
        response = self.client.get(f'/i/{self.institution.slug}/dashboard/')
        
        # Verificar que no es un dashboard funcional
        if response.status_code == 200:
            content = response.content.decode('utf-8').lower()
            # No debe contener acciones típicas de dashboard institucional
            self.assertFalse(
                'nuevo curso' in content and 'importar csv' in content,
                "Dashboard de institución no debe ser funcional"
            )
    
    def test_institution_routes_deprecated(self):
        """Las rutas de gestión de institución deben redirigir"""
        self.client.login(username='test_institution', password='inst123')
        
        routes_to_test = [
            f'/i/{self.institution.slug}/institution/courses/',
            f'/i/{self.institution.slug}/institution/courses/new/',
            f'/i/{self.institution.slug}/institution/agents/',
            f'/i/{self.institution.slug}/institution/errors/',
        ]
        
        for route in routes_to_test:
            response = self.client.get(route)
            # Debe redirigir (no mostrar contenido funcional)
            self.assertEqual(
                response.status_code, 302,
                f"Route {route} should redirect to dashboard"
            )
    
    # ============================================
    # TESTS: TUTOR TIENE DASHBOARD FUNCIONAL
    # ============================================
    
    def test_tutor_can_access_dashboard(self):
        """El tutor debe poder acceder a su dashboard"""
        self.client.login(username='test_tutor', password='tutor123')
        response = self.client.get(f'/i/{self.institution.slug}/dashboard/tutor/')
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Tutor', content)
    
    def test_tutor_redirects_correctly(self):
        """El tutor debe ser redirigido a su dashboard"""
        self.client.login(username='test_tutor', password='tutor123')
        response = self.client.get('/dashboard/')
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dashboard/tutor/', response.url)
    
    def test_tutor_cannot_access_admin(self):
        """El tutor NO debe poder acceder a Django Admin"""
        self.client.login(username='test_tutor', password='tutor123')
        response = self.client.get('/admin/')
        
        # Debe redirigir al login de admin
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
    
    # ============================================
    # TESTS: ESTUDIANTE TIENE DASHBOARD FUNCIONAL
    # ============================================
    
    def test_student_can_access_dashboard(self):
        """El estudiante debe poder acceder a su dashboard"""
        self.client.login(username='test_student', password='student123')
        response = self.client.get(f'/i/{self.institution.slug}/dashboard/student/')
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Hola', content)  # Mensaje de bienvenida
    
    def test_student_redirects_correctly(self):
        """El estudiante debe ser redirigido a su dashboard"""
        self.client.login(username='test_student', password='student123')
        response = self.client.get('/dashboard/')
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dashboard/student/', response.url)
    
    def test_student_cannot_access_admin(self):
        """El estudiante NO debe poder acceder a Django Admin"""
        self.client.login(username='test_student', password='student123')
        response = self.client.get('/admin/')
        
        # Debe redirigir al login de admin
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
    
    def test_student_cannot_access_tutor_routes(self):
        """El estudiante NO debe poder acceder a rutas de tutor"""
        self.client.login(username='test_student', password='student123')
        
        routes_to_test = [
            f'/i/{self.institution.slug}/tutor/groups/',
            f'/i/{self.institution.slug}/tutor/students/',
            f'/i/{self.institution.slug}/tutor/activities/new/',
        ]
        
        for route in routes_to_test:
            response = self.client.get(route)
            # Debe redirigir o mostrar error de acceso
            self.assertIn(
                response.status_code, [302, 403],
                f"Student should not access {route}"
            )
    
    # ============================================
    # TESTS: VALIDACIÓN DE ROLES EN LOGIN
    # ============================================
    
    def test_login_admin_redirects_to_admin_login(self):
        """El login de admin debe redirigir a /admin/login/"""
        response = self.client.post('/login/', {
            'username': 'test_admin',
            'password': 'admin123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/', response.url)
    
    def test_login_tutor_redirects_to_tutor_dashboard(self):
        """El login de tutor debe redirigir a su dashboard"""
        response = self.client.post('/login/', {
            'username': 'test_tutor',
            'password': 'tutor123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dashboard/tutor/', response.url)
    
    def test_login_student_redirects_to_student_dashboard(self):
        """El login de estudiante debe redirigir a su dashboard"""
        response = self.client.post('/login/', {
            'username': 'test_student',
            'password': 'student123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dashboard/student/', response.url)
    
    def test_login_institution_user_blocked(self):
        """El login de usuario con rol 'institution' debe ser bloqueado"""
        response = self.client.post('/login/', {
            'username': 'test_institution',
            'password': 'inst123'
        })
        
        # Puede mostrar error o redirigir a login con mensaje
        if response.status_code == 200:
            content = response.content.decode('utf-8').lower()
            self.assertTrue(
                'deprecado' in content or 'no válido' in content or 'error' in content,
                "Debe mostrar mensaje de error para rol deprecado"
            )


class URLCleanupTest(TestCase):
    """
    Tests que validan que las URLs obsoletas no existen o redirigen.
    """
    
    def test_no_admin_panel_functional_urls(self):
        """No deben existir URLs funcionales de admin-panel"""
        from django.urls import URLResolver, URLPattern
        from arduino_ide.urls import urlpatterns
        
        admin_panel_patterns = []
        
        def find_admin_panel_urls(patterns, prefix=''):
            for pattern in patterns:
                if isinstance(pattern, URLResolver):
                    find_admin_panel_urls(pattern.url_patterns, prefix + str(pattern.pattern))
                elif isinstance(pattern, URLPattern):
                    full_path = prefix + str(pattern.pattern)
                    if 'admin-panel' in full_path and pattern.callback:
                        # Verificar que no es una vista funcional real
                        callback_name = getattr(pattern.callback, '__name__', '')
                        if callback_name not in ['redirect_to_admin', 'deprecated_redirect']:
                            admin_panel_patterns.append(full_path)
        
        find_admin_panel_urls(urlpatterns)
        
        self.assertEqual(
            len(admin_panel_patterns), 0,
            f"Found functional admin-panel URLs: {admin_panel_patterns}"
        )
