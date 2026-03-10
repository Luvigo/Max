"""
Comando de Django para crear datos de prueba.
Uso: python manage.py create_test_data

REGLA DE PRODUCCIÓN: Este comando NUNCA debe ejecutarse en staging/producción.
Solo crear usuarios desde Django Admin o comandos controlados.
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
import os
from django.utils import timezone
from datetime import timedelta
import random

from editor.models import (
    Institution, Membership, Course, Enrollment, TeachingAssignment,
    Activity, Student, UserRoleHelper, IDEProject, ActivityWorkspace
)


class Command(BaseCommand):
    help = 'Crea datos de prueba: institución, usuarios, cursos, actividades, etc.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina todos los datos de prueba antes de crear nuevos',
        )

    def handle(self, *args, **options):
        # Protección: NUNCA crear usuarios de prueba en producción/staging
        render = os.environ.get('RENDER') == 'true'
        env = os.environ.get('ENV', '').lower()
        if render or env == 'production' or env == 'staging':
            raise CommandError(
                'create_test_data no puede ejecutarse en producción o staging. '
                'Los usuarios solo se crean desde Django Admin o comandos controlados.'
            )

        if options['clear']:
            self.stdout.write(self.style.WARNING('Eliminando datos de prueba existentes...'))
            # Eliminar datos de prueba (cuidado con datos reales)
            Institution.objects.filter(slug__startswith='test-').delete()
            User.objects.filter(username__startswith='test_').delete()
            self.stdout.write(self.style.SUCCESS('Datos de prueba eliminados'))

        self.stdout.write(self.style.SUCCESS('=== Creando datos de prueba ===\n'))

        # 1. Crear Institución
        institution = self.create_institution()
        
        # 2. Crear Usuarios
        admin_user = self.create_admin_user()
        institution_user = self.create_institution_user(institution)
        tutor_user = self.create_tutor_user(institution)
        student_users = self.create_student_users(institution, count=5)
        
        # 3. Crear Cursos
        courses = self.create_courses(institution, tutor_user, count=3)
        
        # 4. Matricular estudiantes en cursos
        self.enroll_students(courses, student_users)
        
        # 5. Crear Actividades
        activities = self.create_activities(courses, count=2)
        
        # 6. Crear workspaces para estudiantes (para probar el botón Entregar)
        self.create_student_workspaces(institution, student_users, activities)
        
        self.stdout.write(self.style.SUCCESS('\n=== Datos de prueba creados exitosamente ==='))
        self.print_summary(institution, admin_user, institution_user, tutor_user, student_users, courses)

    def create_institution(self):
        """Crea una institución de prueba"""
        institution, created = Institution.objects.get_or_create(
            slug='test-institucion',
            defaults={
                'name': 'Institución de Prueba',
                'code': 'TEST001',
                'description': 'Institución de prueba para testing',
                'status': 'active',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Institución creada: {institution.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'→ Institución ya existe: {institution.name}'))
        
        return institution

    def create_admin_user(self):
        """Crea un usuario admin de prueba"""
        user, created = User.objects.get_or_create(
            username='test_admin',
            defaults={
                'email': 'admin@test.com',
                'first_name': 'Admin',
                'last_name': 'Test',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            user.set_password('test123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Admin creado: {user.username} (password: test123)'))
        else:
            self.stdout.write(self.style.WARNING(f'→ Admin ya existe: {user.username}'))
        
        return user

    def create_institution_user(self, institution):
        """Crea un usuario de institución"""
        user, created = User.objects.get_or_create(
            username='test_institucion',
            defaults={
                'email': 'institucion@test.com',
                'first_name': 'Institución',
                'last_name': 'Test',
            }
        )
        
        if created:
            user.set_password('test123')
            user.save()
        
        # Crear membership
        membership, created = Membership.objects.get_or_create(
            user=user,
            institution=institution,
            defaults={
                'role': 'institution',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Usuario Institución creado: {user.username} (password: test123)'))
        else:
            self.stdout.write(self.style.WARNING(f'→ Usuario Institución ya existe: {user.username}'))
        
        return user

    def create_tutor_user(self, institution):
        """Crea un usuario tutor"""
        user, created = User.objects.get_or_create(
            username='test_tutor',
            defaults={
                'email': 'tutor@test.com',
                'first_name': 'Profesor',
                'last_name': 'Test',
            }
        )
        
        if created:
            user.set_password('test123')
            user.save()
        
        # Crear membership
        membership, created = Membership.objects.get_or_create(
            user=user,
            institution=institution,
            defaults={
                'role': 'tutor',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Tutor creado: {user.username} (password: test123)'))
        else:
            self.stdout.write(self.style.WARNING(f'→ Tutor ya existe: {user.username}'))
        
        return user

    def create_student_users(self, institution, count=5):
        """Crea múltiples usuarios estudiantes"""
        students = []
        
        for i in range(1, count + 1):
            user, created = User.objects.get_or_create(
                username=f'test_estudiante{i}',
                defaults={
                    'email': f'estudiante{i}@test.com',
                    'first_name': f'Estudiante',
                    'last_name': f'{i}',
                }
            )
            
            if created:
                user.set_password('test123')
                user.save()
            
            # Crear membership
            membership, created = Membership.objects.get_or_create(
                user=user,
                institution=institution,
                defaults={
                    'role': 'student',
                    'is_active': True,
                }
            )
            
            # Crear perfil de estudiante
            student, created = Student.objects.get_or_create(
                user=user,
                defaults={
                    'student_id': f'EST{i:03d}',
                    'course': None,  # Se asignará después
                    'is_active': True,
                }
            )
            
            students.append(user)
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Estudiante {i} creado: {user.username} (password: test123)'))
        
        return students

    def create_courses(self, institution, tutor, count=3):
        """Crea cursos de prueba"""
        courses = []
        
        course_names = [
            'Programación con Arduino',
            'Robótica Básica',
            'Electrónica Digital'
        ]
        
        grade_levels = ['1ro', '2do', '3ro']
        
        for i in range(min(count, len(course_names))):
            course, created = Course.objects.get_or_create(
                institution=institution,
                code=f'TEST{i+1:03d}',
                defaults={
                    'name': course_names[i],
                    'description': f'Curso de prueba: {course_names[i]}',
                    'grade_level': grade_levels[i],
                    'academic_year': '2024',
                    'status': 'published',
                    'is_active': True,
                    'tutor': tutor,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Curso creado: {course.name}'))
            
            # Crear TeachingAssignment
            assignment, created = TeachingAssignment.objects.get_or_create(
                course=course,
                tutor=tutor,
                defaults={
                    'status': 'active',
                }
            )
            
            courses.append(course)
        
        return courses

    def enroll_students(self, courses, students):
        """Matricula estudiantes en cursos"""
        from editor.models import Enrollment
        
        enrolled_count = 0
        
        for course in courses:
            # Matricular 3-4 estudiantes por curso
            students_for_course = random.sample(students, min(len(students), 4))
            
            for student in students_for_course:
                enrollment, created = Enrollment.objects.get_or_create(
                    course=course,
                    student=student,
                    defaults={
                        'status': 'active',
                    }
                )
                
                if created:
                    enrolled_count += 1
                    # Actualizar el curso del estudiante
                    try:
                        student_profile = Student.objects.get(user=student)
                        if not student_profile.course:
                            student_profile.course = course
                            student_profile.save()
                    except Student.DoesNotExist:
                        pass
        
        if enrolled_count > 0:
            self.stdout.write(self.style.SUCCESS(f'✓ {enrolled_count} matrículas creadas'))

    def create_activities(self, courses, count=2):
        """Crea actividades de prueba"""
        from editor.models import Activity
        
        activity_titles = [
            'Mi primer LED parpadeante',
            'Control de motor con PWM',
            'Sensor de distancia',
            'Sistema de alarmas',
        ]
        
        created_count = 0
        activities = []
        
        for course in courses:
            for i in range(count):
                if created_count >= len(activity_titles):
                    break
                
                title = activity_titles[created_count]
                
                activity, created = Activity.objects.get_or_create(
                    course=course,
                    title=title,
                    defaults={
                        'objective': f'Objetivo: Aprender a programar {title.lower()}',
                        'instructions': f'Instrucciones para {title}:\n1. Conecta los componentes\n2. Carga el código\n3. Prueba el funcionamiento',
                        'deadline': timezone.now() + timedelta(days=7),
                        'status': 'published' if i == 0 else 'draft',
                        'allow_resubmit': True,
                    }
                )
                
                if created:
                    created_count += 1
                    if activity.status == 'published':
                        activity.published_at = timezone.now()
                        activity.save()
                    self.stdout.write(self.style.SUCCESS(f'✓ Actividad creada: {activity.title} (Curso: {course.name})'))
                
                activities.append(activity)
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'✓ Total actividades creadas: {created_count}'))
        
        return activities
    
    def create_student_workspaces(self, institution, students, activities):
        """Crea workspaces para que los estudiantes puedan trabajar en actividades"""
        created_count = 0
        
        # Solo actividades publicadas
        published_activities = [a for a in activities if a.status == 'published']
        
        for activity in published_activities:
            # Obtener estudiantes matriculados en el curso de la actividad
            enrolled_students = Enrollment.objects.filter(
                course=activity.course,
                status='active'
            ).values_list('student', flat=True)
            
            for student in students:
                if student.id in enrolled_students:
                    # Crear proyecto IDE
                    project, created = IDEProject.objects.get_or_create(
                        owner=student,
                        institution=institution,
                        name=f'{activity.title} - {student.first_name}',
                        defaults={
                            'blockly_xml': '',
                            'arduino_code': '',
                        }
                    )
                    
                    # Crear workspace de actividad
                    workspace, ws_created = ActivityWorkspace.objects.get_or_create(
                        activity=activity,
                        student=student,
                        defaults={
                            'project': project,
                            'status': 'in_progress',
                        }
                    )
                    
                    if ws_created:
                        created_count += 1
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'✓ {created_count} workspaces de actividad creados'))

    def print_summary(self, institution, admin_user, institution_user, tutor_user, student_users, courses):
        """Imprime resumen de los datos creados"""
        self.stdout.write(self.style.SUCCESS('\n=== RESUMEN DE DATOS DE PRUEBA ===\n'))
        
        self.stdout.write(f'📚 Institución: {institution.name} (slug: {institution.slug})')
        self.stdout.write(f'   URL: /i/{institution.slug}/\n')
        
        self.stdout.write('👥 Usuarios creados:')
        self.stdout.write(f'   🔑 Admin: {admin_user.username} / test123')
        self.stdout.write(f'   🏫 Institución: {institution_user.username} / test123')
        self.stdout.write(f'   👨‍🏫 Tutor: {tutor_user.username} / test123')
        self.stdout.write(f'   👨‍🎓 Estudiantes: {len(student_users)} usuarios (test_estudiante1 a test_estudiante{len(student_users)} / test123)\n')
        
        self.stdout.write(f'📖 Cursos: {len(courses)} cursos creados')
        for course in courses:
            enrollments = Enrollment.objects.filter(course=course).count()
            activities = Activity.objects.filter(course=course).count()
            self.stdout.write(f'   - {course.name} ({enrollments} estudiantes, {activities} actividades)')
        
        total_activities = Activity.objects.filter(course__institution=institution).count()
        self.stdout.write(f'\n📝 Actividades: {total_activities} actividades totales\n')
        
        self.stdout.write(self.style.SUCCESS('✅ Todos los usuarios tienen la contraseña: test123'))
        self.stdout.write(self.style.SUCCESS('✅ Puedes iniciar sesión en: /login/'))
