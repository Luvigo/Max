"""
MODULO 4: Tests de Grupos y Estudiantes

Tests para:
- StudentGroup model
- Student model (extendido)
- Vistas de tutor para grupos y estudiantes
- Vista de estudiante para contexto
- Segregacion de datos
- Admin form: InstitutionIdOrCodeField (acepta UUID o institution.code)
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from editor.models import Institution, Membership, TutorProfile, StudentGroup, Student
from editor.forms import InstitutionIdOrCodeField, _institution_from_value


class InstitutionIdOrCodeFieldTest(TestCase):
    """Tests para InstitutionIdOrCodeField - acepta UUID o institution.code"""

    def setUp(self):
        self.institution = Institution.objects.create(
            name='La Concepción',
            slug='la-concepcion',
            code='LCONCEPT',
            status='active'
        )
        self.queryset = Institution.objects.all()

    def test_resolves_by_uuid(self):
        """Acepta UUID (pk) de la institución"""
        inst = _institution_from_value(str(self.institution.pk), self.queryset)
        self.assertEqual(inst, self.institution)

    def test_resolves_by_code(self):
        """Acepta institution.code cuando no es UUID"""
        inst = _institution_from_value('LCONCEPT', self.queryset)
        self.assertEqual(inst, self.institution)

    def test_returns_none_for_empty(self):
        """Valores vacíos retornan None"""
        self.assertIsNone(_institution_from_value('', self.queryset))
        self.assertIsNone(_institution_from_value(None, self.queryset))

    def test_returns_none_for_invalid_code(self):
        """Código inexistente retorna None"""
        self.assertIsNone(_institution_from_value('NOEXIST', self.queryset))

    def test_field_valid_with_uuid(self):
        """InstitutionIdOrCodeField valida correctamente con UUID"""
        field = InstitutionIdOrCodeField(queryset=self.queryset, required=True)
        result = field.clean(str(self.institution.pk))
        self.assertEqual(result, self.institution)

    def test_field_valid_with_code(self):
        """InstitutionIdOrCodeField valida correctamente con institution.code"""
        field = InstitutionIdOrCodeField(queryset=self.queryset, required=True)
        result = field.clean('LCONCEPT')
        self.assertEqual(result, self.institution)

    def test_field_invalid_raises(self):
        """InstitutionIdOrCodeField levanta ValidationError para valor inválido"""
        from django import forms
        field = InstitutionIdOrCodeField(queryset=self.queryset, required=True)
        with self.assertRaises(forms.ValidationError):
            field.clean('CODIGO_INEXISTENTE')


class StudentGroupAdminFormTest(TestCase):
    """Tests para creación de Grupo de Estudiantes desde admin"""

    def setUp(self):
        self.institution = Institution.objects.create(
            name='La Concepción',
            slug='la-concepcion',
            code='LCONCEPT',
            status='active'
        )
        self.tutor_user = User.objects.create_user(
            username='tutor_admin',
            email='tutor@test.com',
            password='test123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )

    def test_create_group_with_institution_by_uuid(self):
        """Crear grupo con institución seleccionada por UUID guarda sin error"""
        from editor.forms import StudentGroupAdminForm
        data = {
            'institution': str(self.institution.pk),
            'tutor': self.tutor_user.pk,
            'name': 'Grupo A',
            'code': 'G1-2026',
            'academic_year': '2026',
            'max_students': 30,
            'status': 'active',
        }
        form = StudentGroupAdminForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)
        group = form.save()
        self.assertEqual(group.institution, self.institution)

    def test_create_group_with_institution_by_code(self):
        """Crear grupo con institución por código (no UUID) guarda sin error"""
        from editor.forms import StudentGroupAdminForm
        data = {
            'institution': 'LCONCEPT',
            'tutor': self.tutor_user.pk,
            'name': 'Grupo B',
            'code': 'G2-2026',
            'academic_year': '2026',
            'max_students': 30,
            'status': 'active',
        }
        form = StudentGroupAdminForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)
        group = form.save()
        self.assertEqual(group.institution, self.institution)

    def test_group_code_unique_per_institution(self):
        """Constraint unique_together (institution, code) se respeta"""
        StudentGroup.objects.create(
            institution=self.institution,
            tutor=self.tutor_user,
            name='Grupo Original',
            code='G1-2026',
            academic_year='2026',
            status='active',
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            StudentGroup.objects.create(
                institution=self.institution,
                tutor=self.tutor_user,
                name='Otro Grupo',
                code='G1-2026',
                academic_year='2026',
                status='active',
            )


class StudentGroupModelTest(TestCase):
    """Tests para el modelo StudentGroup"""

    def setUp(self):
        self.institution = Institution.objects.create(
            name='Test Institution',
            slug='test-inst',
            code='TEST001',
            status='active'
        )
        
        self.tutor_user = User.objects.create_user(
            username='test_tutor',
            email='tutor@test.com',
            password='test123'
        )
        
        self.group = StudentGroup.objects.create(
            institution=self.institution,
            tutor=self.tutor_user,
            name='Grupo A',
            code='GA-2026',
            academic_year='2026',
            max_students=5,
            status='active'
        )
    
    def test_group_creation(self):
        """StudentGroup se crea correctamente"""
        self.assertEqual(self.group.name, 'Grupo A')
        self.assertEqual(self.group.code, 'GA-2026')
        self.assertEqual(self.group.institution, self.institution)
        self.assertEqual(self.group.tutor, self.tutor_user)
    
    def test_is_active_property(self):
        """is_active refleja el status"""
        self.assertTrue(self.group.is_active)
        
        self.group.status = 'inactive'
        self.group.save()
        self.assertFalse(self.group.is_active)
    
    def test_get_students_count(self):
        """get_students_count cuenta estudiantes activos"""
        self.assertEqual(self.group.get_students_count(), 0)
        
        # Crear estudiante
        student_user = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='test123'
        )
        Student.objects.create(
            user=student_user,
            student_id='EST-001',
            institution=self.institution,
            group=self.group,
            is_active=True
        )
        
        self.assertEqual(self.group.get_students_count(), 1)
    
    def test_get_available_slots(self):
        """get_available_slots calcula espacios disponibles"""
        self.assertEqual(self.group.get_available_slots(), 5)
        
        # Agregar estudiantes
        for i in range(3):
            user = User.objects.create_user(
                username=f'student{i}',
                email=f'student{i}@test.com',
                password='test123'
            )
            Student.objects.create(
                user=user,
                student_id=f'EST-{i}',
                institution=self.institution,
                group=self.group,
                is_active=True
            )
        
        self.assertEqual(self.group.get_available_slots(), 2)
    
    def test_is_full(self):
        """is_full detecta grupo lleno"""
        self.assertFalse(self.group.is_full())
        
        # Llenar grupo
        for i in range(5):
            user = User.objects.create_user(
                username=f'student{i}',
                email=f'student{i}@test.com',
                password='test123'
            )
            Student.objects.create(
                user=user,
                student_id=f'EST-{i}',
                institution=self.institution,
                group=self.group,
                is_active=True
            )
        
        self.assertTrue(self.group.is_full())


class StudentModelTest(TestCase):
    """Tests para el modelo Student extendido"""

    def setUp(self):
        self.institution = Institution.objects.create(
            name='Test Institution',
            slug='test-inst',
            code='TEST002',
            status='active'
        )
        
        self.tutor_user = User.objects.create_user(
            username='test_tutor',
            email='tutor@test.com',
            password='test123'
        )
        
        self.group = StudentGroup.objects.create(
            institution=self.institution,
            tutor=self.tutor_user,
            name='Grupo A',
            code='GA-2026',
            academic_year='2026',
            status='active'
        )
        
        self.student_user = User.objects.create_user(
            username='test_student',
            email='student@test.com',
            password='test123',
            first_name='Juan',
            last_name='Perez'
        )
        
        self.student = Student.objects.create(
            user=self.student_user,
            student_id='EST-001',
            institution=self.institution,
            group=self.group,
            tutor=self.tutor_user,
            is_active=True
        )
    
    def test_student_creation(self):
        """Student se crea correctamente"""
        self.assertEqual(self.student.student_id, 'EST-001')
        self.assertEqual(self.student.institution, self.institution)
        self.assertEqual(self.student.group, self.group)
        self.assertEqual(self.student.tutor, self.tutor_user)
    
    def test_full_name_property(self):
        """full_name retorna nombre completo"""
        self.assertEqual(self.student.full_name, 'Juan Perez')
    
    def test_email_property(self):
        """email retorna email del usuario"""
        self.assertEqual(self.student.email, 'student@test.com')
    
    def test_get_institution(self):
        """get_institution busca institucion en orden correcto"""
        # Con institucion directa
        self.assertEqual(self.student.get_institution(), self.institution)
        
        # Sin institucion directa, via grupo
        self.student.institution = None
        self.student.save()
        self.assertEqual(self.student.get_institution(), self.institution)
    
    def test_get_tutor(self):
        """get_tutor busca tutor en orden correcto"""
        # Con tutor directo
        self.assertEqual(self.student.get_tutor(), self.tutor_user)
        
        # Sin tutor directo, via grupo
        self.student.tutor = None
        self.student.save()
        self.assertEqual(self.student.get_tutor(), self.tutor_user)
    
    def test_get_group_name(self):
        """get_group_name retorna nombre del grupo"""
        self.assertEqual(self.student.get_group_name(), 'Grupo A')
        
        self.student.group = None
        self.student.save()
        self.assertEqual(self.student.get_group_name(), 'Sin grupo')
    
    def test_can_login(self):
        """can_login verifica estado del estudiante y usuario"""
        self.assertTrue(self.student.can_login())
        
        self.student.is_active = False
        self.student.save()
        self.assertFalse(self.student.can_login())


class TutorGroupViewsTest(TestCase):
    """Tests para vistas de grupos del tutor"""

    def setUp(self):
        self.client = Client()

        self.institution = Institution.objects.create(
            name='Test Institution',
            slug='test-inst',
            code='TEST003',
            status='active'
        )
        
        self.tutor_user = User.objects.create_user(
            username='test_tutor',
            email='tutor@test.com',
            password='test123'
        )
        
        Membership.objects.create(
            user=self.tutor_user,
            institution=self.institution,
            role='tutor',
            is_active=True
        )
        
        self.group = StudentGroup.objects.create(
            institution=self.institution,
            tutor=self.tutor_user,
            name='Grupo A',
            code='GA-2026',
            academic_year='2026',
            status='active'
        )
        
        # Otro tutor para probar segregacion
        self.other_tutor = User.objects.create_user(
            username='other_tutor',
            email='other@test.com',
            password='test123'
        )
        
        Membership.objects.create(
            user=self.other_tutor,
            institution=self.institution,
            role='tutor',
            is_active=True
        )
        
        self.other_group = StudentGroup.objects.create(
            institution=self.institution,
            tutor=self.other_tutor,
            name='Grupo B',
            code='GB-2026',
            academic_year='2026',
            status='active'
        )
    
    def test_tutor_can_list_own_groups(self):
        """Tutor puede listar sus grupos"""
        self.client.login(username='test_tutor', password='test123')
        response = self.client.get(
            reverse('editor:tutor_groups_list', kwargs={'institution_slug': 'test-inst'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Grupo A')
        self.assertNotContains(response, 'Grupo B')  # No ver grupos de otro tutor
    
    def test_tutor_can_view_own_group(self):
        """Tutor puede ver detalle de su grupo"""
        self.client.login(username='test_tutor', password='test123')
        response = self.client.get(
            reverse('editor:tutor_group_detail', kwargs={
                'institution_slug': 'test-inst',
                'group_id': self.group.id
            })
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Grupo A')
    
    def test_tutor_cannot_view_other_group(self):
        """Tutor NO puede ver grupo de otro tutor"""
        self.client.login(username='test_tutor', password='test123')
        response = self.client.get(
            reverse('editor:tutor_group_detail', kwargs={
                'institution_slug': 'test-inst',
                'group_id': self.other_group.id
            })
        )
        self.assertEqual(response.status_code, 404)


class StudentContextViewTest(TestCase):
    """Tests para vista de contexto del estudiante"""

    def setUp(self):
        self.client = Client()

        self.institution = Institution.objects.create(
            name='Test Institution',
            slug='test-inst',
            code='TEST004',
            status='active'
        )
        
        self.tutor_user = User.objects.create_user(
            username='test_tutor',
            email='tutor@test.com',
            password='test123'
        )
        
        self.group = StudentGroup.objects.create(
            institution=self.institution,
            tutor=self.tutor_user,
            name='Grupo A',
            code='GA-2026',
            academic_year='2026',
            status='active'
        )
        
        self.student_user = User.objects.create_user(
            username='test_student',
            email='student@test.com',
            password='test123',
            first_name='Juan',
            last_name='Perez'
        )
        
        self.student = Student.objects.create(
            user=self.student_user,
            student_id='EST-001',
            institution=self.institution,
            group=self.group,
            tutor=self.tutor_user,
            is_active=True
        )
        
        Membership.objects.create(
            user=self.student_user,
            institution=self.institution,
            role='student',
            is_active=True
        )
    
    def test_student_can_view_context(self):
        """Estudiante puede ver su contexto"""
        self.client.login(username='test_student', password='test123')
        response = self.client.get(
            reverse('editor:student_my_context', kwargs={'institution_slug': 'test-inst'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Juan Perez')
        self.assertContains(response, 'Grupo A')
        self.assertContains(response, 'EST-001')
    
    def test_tutor_cannot_view_student_context(self):
        """Tutor NO puede ver contexto de estudiante"""
        self.client.login(username='test_tutor', password='test123')
        response = self.client.get(
            reverse('editor:student_my_context', kwargs={'institution_slug': 'test-inst'})
        )
        # Debe redirigir o dar 403
        self.assertIn(response.status_code, [302, 403])
