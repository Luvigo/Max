"""
WSGI config for arduino_ide project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arduino_ide.settings')

application = get_wsgi_application()


# Crear usuarios de prueba automáticamente al iniciar (para Render/producción)
def create_initial_users():
    """Crea usuarios de prueba si no existen"""
    import django
    from django.db import connection
    
    # Verificar que Django está listo y la BD está disponible
    try:
        # Intentar hacer una query simple para verificar conexión
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as e:
        print(f"[WSGI] Base de datos no disponible: {e}")
        return
    
    try:
        from django.contrib.auth.models import User
        from editor.models import Institution, Membership, Course, Student, Enrollment, TeachingAssignment
        
        print("[WSGI] Verificando/creando datos iniciales...")
        
        # Crear usuario admin si no existe
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@maxide.com',
                password='admin123',
                first_name='Admin',
                last_name='MAX-IDE'
            )
            print("[WSGI] Usuario admin creado")
        
        # Crear institución de prueba
        institution, created = Institution.objects.get_or_create(
            slug='test-institucion',
            defaults={
                'name': 'Institución de Prueba',
                'code': 'TEST001',
                'status': 'active',
            }
        )
        if created:
            print("[WSGI] Institución de prueba creada")
        
        # Crear usuarios de prueba
        test_users = [
            ('test_admin', 'admin@test.com', 'Admin', 'Test', True, True, None),
            ('test_institucion', 'institucion@test.com', 'Institución', 'Test', False, False, 'institution'),
            ('test_tutor', 'tutor@test.com', 'Profesor', 'Test', False, False, 'tutor'),
            ('test_estudiante1', 'estudiante1@test.com', 'Estudiante', '1', False, False, 'student'),
            ('test_estudiante2', 'estudiante2@test.com', 'Estudiante', '2', False, False, 'student'),
            ('test_estudiante3', 'estudiante3@test.com', 'Estudiante', '3', False, False, 'student'),
        ]
        
        for username, email, first_name, last_name, is_staff, is_superuser, role in test_users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_staff': is_staff,
                    'is_superuser': is_superuser,
                }
            )
            if created:
                user.set_password('test123')
                user.save()
                print(f"[WSGI] Usuario {username} creado")
            else:
                # Si existe pero no tiene password usable, resetear
                if not user.has_usable_password():
                    user.set_password('test123')
                    user.save()
                    print(f"[WSGI] Password reseteado para {username}")
            
            # Crear membresía si tiene rol
            if role:
                membership, m_created = Membership.objects.get_or_create(
                    user=user,
                    institution=institution,
                    defaults={
                        'role': role,
                        'is_active': True
                    }
                )
                if m_created:
                    print(f"[WSGI] Membresía de {username} creada")
        
        # Crear curso de prueba
        tutor_user = User.objects.filter(username='test_tutor').first()
        course, created = Course.objects.get_or_create(
            institution=institution,
            code='ARDUINO101',
            defaults={
                'name': 'Programación con Arduino',
                'description': 'Curso introductorio de Arduino',
                'grade_level': '1ro',
                'academic_year': '2024',
                'status': 'published',
                'tutor': tutor_user,
            }
        )
        if created:
            print("[WSGI] Curso de prueba creado")
            
            # Asignar tutor
            if tutor_user:
                TeachingAssignment.objects.get_or_create(
                    course=course,
                    tutor=tutor_user,
                    defaults={'status': 'active'}
                )
        
        # Matricular estudiantes
        for i in range(1, 4):
            student_user = User.objects.filter(username=f'test_estudiante{i}').first()
            if student_user:
                Enrollment.objects.get_or_create(
                    course=course,
                    student=student_user,
                    defaults={'status': 'active'}
                )
        
        print("[WSGI] ✅ Datos iniciales verificados/creados correctamente")
        
    except Exception as e:
        import traceback
        print(f"[WSGI] Error creando usuarios iniciales: {e}")
        traceback.print_exc()


# Ejecutar creación de usuarios al iniciar
# Siempre intentar crear porque es idempotente (usa get_or_create)
try:
    create_initial_users()
except Exception as e:
    import traceback
    print(f"[WSGI] Error en inicialización: {e}")
    traceback.print_exc()