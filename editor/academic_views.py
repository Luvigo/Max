"""
Vistas del Módulo 2: Estructura Académica multi-tenant
"""
import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.db.models import Count, Q

from .models import Institution, Course, Enrollment, TeachingAssignment, Membership
from .forms import CourseForm, AssignTutorForm, EnrollmentForm, CSVImportForm
from .mixins import InstitutionScopedMixin, RoleRequiredMixin
from .models import UserRoleHelper


# ============================================
# VISTAS DE INSTITUCIÓN
# ============================================

@login_required
def institution_courses_list(request, institution_slug):
    """Lista de cursos de la institución"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para ver los cursos.')
        return redirect('editor:dashboard')
    
    courses = Course.objects.filter(
        institution=institution
    ).annotate(
        students_count=Count('enrollments', filter=Q(enrollments__status='active')),
        tutors_count=Count('teaching_assignments', filter=Q(teaching_assignments__status='active'))
    ).order_by('-academic_year', 'name')
    
    context = {
        'institution': institution,
        'courses': courses,
        'user_role': UserRoleHelper.get_user_role(request.user, institution),
    }
    return render(request, 'editor/academic/institution/courses_list.html', context)


@login_required
def institution_course_create(request, institution_slug):
    """Crear nuevo curso"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para crear cursos.')
        return redirect('editor:institution_courses_list', institution_slug=institution_slug)
    
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.institution = institution
            course.save()
            messages.success(request, f'Curso "{course.name}" creado exitosamente.')
            return redirect('editor:institution_courses_list', institution_slug=institution_slug)
    else:
        form = CourseForm()
    
    context = {
        'institution': institution,
        'form': form,
        'action': 'Crear',
    }
    return render(request, 'editor/academic/institution/course_form.html', context)


@login_required
def institution_course_edit(request, institution_slug, course_id):
    """Editar curso existente"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    course = get_object_or_404(Course, id=course_id, institution=institution)
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para editar cursos.')
        return redirect('editor:institution_courses_list', institution_slug=institution_slug)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Curso "{course.name}" actualizado exitosamente.')
            return redirect('editor:institution_courses_list', institution_slug=institution_slug)
    else:
        form = CourseForm(instance=course)
    
    context = {
        'institution': institution,
        'course': course,
        'form': form,
        'action': 'Editar',
    }
    return render(request, 'editor/academic/institution/course_form.html', context)


@login_required
def institution_course_assign_tutor(request, institution_slug, course_id):
    """Asignar tutor a un curso"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    course = get_object_or_404(Course, id=course_id, institution=institution)
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para asignar tutores.')
        return redirect('editor:institution_courses_list', institution_slug=institution_slug)
    
    if request.method == 'POST':
        form = AssignTutorForm(request.POST, institution=institution)
        if form.is_valid():
            tutor = form.cleaned_data['tutor']
            
            # Verificar que el tutor pertenece a la institución
            if not Membership.objects.filter(
                user=tutor,
                institution=institution,
                role__in=['tutor', 'institution', 'admin'],
                is_active=True
            ).exists():
                messages.error(request, 'El tutor seleccionado no pertenece a esta institución.')
                return redirect('editor:institution_course_assign_tutor', institution_slug=institution_slug, course_id=course_id)
            
            # Crear o actualizar asignación
            assignment, created = TeachingAssignment.objects.get_or_create(
                course=course,
                tutor=tutor,
                defaults={'status': 'active'}
            )
            
            if not created:
                assignment.status = 'active'
                assignment.save()
            
            messages.success(request, f'Tutor "{tutor.get_full_name() or tutor.username}" asignado exitosamente.')
            return redirect('editor:institution_courses_list', institution_slug=institution_slug)
    else:
        form = AssignTutorForm(institution=institution)
    
    # Obtener tutores ya asignados
    assigned_tutors = course.get_assigned_tutors()
    
    context = {
        'institution': institution,
        'course': course,
        'form': form,
        'assigned_tutors': assigned_tutors,
    }
    return render(request, 'editor/academic/institution/assign_tutor.html', context)


@login_required
def institution_enroll_student(request, institution_slug, course_id):
    """Matricular estudiante en un curso"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    course = get_object_or_404(Course, id=course_id, institution=institution)
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para matricular estudiantes.')
        return redirect('editor:institution_courses_list', institution_slug=institution_slug)
    
    if request.method == 'POST':
        form = EnrollmentForm(request.POST, institution=institution)
        if form.is_valid():
            student = form.cleaned_data['student']
            
            # Verificar que el estudiante pertenece a la institución
            if not Membership.objects.filter(
                user=student,
                institution=institution,
                role='student',
                is_active=True
            ).exists():
                messages.error(request, 'El estudiante seleccionado no pertenece a esta institución.')
                return redirect('editor:institution_enroll_student', institution_slug=institution_slug, course_id=course_id)
            
            # Crear o actualizar matrícula
            enrollment, created = Enrollment.objects.get_or_create(
                course=course,
                student=student,
                defaults={
                    'status': form.cleaned_data['status'],
                    'notes': form.cleaned_data['notes']
                }
            )
            
            if not created:
                enrollment.status = form.cleaned_data['status']
                enrollment.notes = form.cleaned_data['notes']
                enrollment.save()
            
            # También actualizar Student.course si existe y no tiene curso asignado
            from .models import Student
            try:
                student_profile = Student.objects.get(user=student)
                if not student_profile.course:
                    student_profile.course = course
                    student_profile.save()
            except Student.DoesNotExist:
                # Crear perfil de Student si no existe
                Student.objects.create(
                    user=student,
                    student_id=f'AUTO-{student.id}',
                    course=course,
                    is_active=True
                )
            
            messages.success(request, f'Estudiante "{student.get_full_name() or student.username}" matriculado exitosamente.')
            return redirect('editor:institution_course_detail', institution_slug=institution_slug, course_id=course_id)
    else:
        form = EnrollmentForm(institution=institution)
    
    context = {
        'institution': institution,
        'course': course,
        'form': form,
    }
    return render(request, 'editor/academic/institution/enroll_student.html', context)


@login_required
def institution_import_csv(request, institution_slug):
    """Importar estudiantes desde CSV"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para importar estudiantes.')
        return redirect('editor:institution_courses_list', institution_slug=institution_slug)
    
    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            try:
                # Leer CSV
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                
                created_count = 0
                updated_count = 0
                errors = []
                
                with transaction.atomic():
                    for row_num, row in enumerate(reader, start=2):  # Empezar en 2 porque la fila 1 es header
                        try:
                            username = row.get('username', '').strip()
                            email = row.get('email', '').strip()
                            first_name = row.get('first_name', '').strip()
                            last_name = row.get('last_name', '').strip()
                            student_id = row.get('student_id', '').strip()
                            
                            if not username:
                                errors.append(f'Fila {row_num}: username es requerido')
                                continue
                            
                            if not email:
                                errors.append(f'Fila {row_num}: email es requerido')
                                continue
                            
                            # Crear o actualizar usuario
                            user, created = User.objects.get_or_create(
                                username=username,
                                defaults={
                                    'email': email,
                                    'first_name': first_name,
                                    'last_name': last_name,
                                }
                            )
                            
                            if not created:
                                user.email = email
                                user.first_name = first_name
                                user.last_name = last_name
                                user.save()
                                updated_count += 1
                            else:
                                created_count += 1
                            
                            # Crear membresía si no existe
                            membership, _ = Membership.objects.get_or_create(
                                user=user,
                                institution=institution,
                                defaults={
                                    'role': 'student',
                                    'is_active': True
                                }
                            )
                            
                        except Exception as e:
                            errors.append(f'Fila {row_num}: {str(e)}')
                
                if errors:
                    messages.warning(request, f'Importación completada con {len(errors)} errores. Ver detalles en la consola.')
                    for error in errors[:10]:  # Mostrar solo los primeros 10 errores
                        messages.warning(request, error)
                else:
                    messages.success(request, f'Importación exitosa: {created_count} creados, {updated_count} actualizados.')
                
                return redirect('editor:institution_courses_list', institution_slug=institution_slug)
                
            except Exception as e:
                messages.error(request, f'Error al procesar el archivo CSV: {str(e)}')
    else:
        form = CSVImportForm()
    
    context = {
        'institution': institution,
        'form': form,
    }
    return render(request, 'editor/academic/institution/import_csv.html', context)


@login_required
def institution_course_detail(request, institution_slug, course_id):
    """Detalle de curso con estudiantes y tutores"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    course = get_object_or_404(Course, id=course_id, institution=institution)
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para ver este curso.')
        return redirect('editor:institution_courses_list', institution_slug=institution_slug)
    
    enrollments = Enrollment.objects.filter(course=course, status='active').select_related('student')
    assignments = TeachingAssignment.objects.filter(course=course, status='active').select_related('tutor')
    
    context = {
        'institution': institution,
        'course': course,
        'enrollments': enrollments,
        'assignments': assignments,
    }
    return render(request, 'editor/academic/institution/course_detail.html', context)


# ============================================
# VISTAS DE TUTOR
# ============================================

@login_required
def tutor_courses_list(request, institution_slug):
    """Lista de cursos asignados al tutor"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution', 'tutor'], institution):
        messages.error(request, 'No tienes permisos para ver cursos.')
        return redirect('editor:dashboard')
    
    # Obtener cursos asignados al tutor
    courses = Course.objects.filter(
        institution=institution,
        teaching_assignments__tutor=request.user,
        teaching_assignments__status='active'
    ).annotate(
        students_count=Count('enrollments', filter=Q(enrollments__status='active'))
    ).distinct().order_by('-academic_year', 'name')
    
    context = {
        'institution': institution,
        'courses': courses,
        'user_role': UserRoleHelper.get_user_role(request.user, institution),
    }
    return render(request, 'editor/academic/tutor/courses_list.html', context)


@login_required
def tutor_course_roster(request, institution_slug, course_id):
    """Roster (lista de estudiantes) de un curso"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    course = get_object_or_404(Course, id=course_id, institution=institution)
    
    # Verificar que el tutor está asignado al curso
    if not TeachingAssignment.objects.filter(
        course=course,
        tutor=request.user,
        status='active'
    ).exists() and not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para ver este curso.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    enrollments = Enrollment.objects.filter(
        course=course,
        status='active'
    ).select_related('student').order_by('student__last_name', 'student__first_name')
    
    context = {
        'institution': institution,
        'course': course,
        'enrollments': enrollments,
    }
    return render(request, 'editor/academic/tutor/course_roster.html', context)


@login_required
def tutor_course_create(request, institution_slug):
    """Tutor crea un nuevo curso"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution', 'tutor'], institution):
        messages.error(request, 'No tienes permisos para crear cursos.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.institution = institution
            course.tutor = request.user
            course.save()
            
            # Auto-asignar al tutor que lo crea
            TeachingAssignment.objects.create(
                course=course,
                tutor=request.user,
                status='active'
            )
            
            messages.success(request, f'Curso "{course.name}" creado exitosamente.')
            return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    else:
        form = CourseForm()
    
    context = {
        'institution': institution,
        'form': form,
        'action': 'Crear',
    }
    return render(request, 'editor/academic/tutor/course_form.html', context)


@login_required
def tutor_student_create(request, institution_slug):
    """Tutor crea un nuevo estudiante con usuario"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution', 'tutor'], institution):
        messages.error(request, 'No tienes permisos para crear estudiantes.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    # Obtener cursos del tutor para asignar
    tutor_courses = Course.objects.filter(
        institution=institution,
        teaching_assignments__tutor=request.user,
        teaching_assignments__status='active'
    )
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '').strip()
        student_id = request.POST.get('student_id', '').strip()
        course_id = request.POST.get('course', '')
        
        errors = []
        
        if not username:
            errors.append('El nombre de usuario es requerido.')
        elif User.objects.filter(username=username).exists():
            errors.append('El nombre de usuario ya existe.')
        
        if not email:
            errors.append('El email es requerido.')
        elif User.objects.filter(email=email).exists():
            errors.append('El email ya está registrado.')
        
        if not password or len(password) < 4:
            errors.append('La contraseña debe tener al menos 4 caracteres.')
        
        if not student_id:
            errors.append('El ID de estudiante es requerido.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                with transaction.atomic():
                    # Crear usuario
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name
                    )
                    
                    # Crear membership como estudiante
                    Membership.objects.create(
                        user=user,
                        institution=institution,
                        role='student',
                        is_active=True
                    )
                    
                    # Crear perfil de estudiante
                    from .models import Student
                    student = Student.objects.create(
                        user=user,
                        student_id=student_id,
                        is_active=True
                    )
                    
                    # Si se seleccionó un curso, matricular
                    if course_id:
                        course = Course.objects.get(id=course_id, institution=institution)
                        Enrollment.objects.create(
                            course=course,
                            student=user,
                            status='active'
                        )
                        student.course = course
                        student.save()
                    
                    messages.success(request, f'Estudiante "{username}" creado exitosamente. Puede iniciar sesión con la contraseña que definiste.')
                    return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
                    
            except Exception as e:
                messages.error(request, f'Error al crear estudiante: {str(e)}')
    
    context = {
        'institution': institution,
        'courses': tutor_courses,
    }
    return render(request, 'editor/academic/tutor/student_form.html', context)


@login_required
def tutor_enroll_student(request, institution_slug, course_id):
    """Tutor matricula estudiante en su curso"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    course = get_object_or_404(Course, id=course_id, institution=institution)
    
    # Verificar que el tutor está asignado al curso
    if not TeachingAssignment.objects.filter(
        course=course,
        tutor=request.user,
        status='active'
    ).exists() and not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para matricular en este curso.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    # Obtener estudiantes de la institución que NO están matriculados en este curso
    enrolled_ids = Enrollment.objects.filter(course=course).values_list('student_id', flat=True)
    available_students = User.objects.filter(
        memberships__institution=institution,
        memberships__role='student',
        memberships__is_active=True
    ).exclude(id__in=enrolled_ids)
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        
        if student_id:
            try:
                student = User.objects.get(id=student_id)
                
                # Verificar que es estudiante de la institución
                if not Membership.objects.filter(
                    user=student,
                    institution=institution,
                    role='student',
                    is_active=True
                ).exists():
                    messages.error(request, 'El usuario no es estudiante de esta institución.')
                else:
                    # Crear matrícula
                    Enrollment.objects.get_or_create(
                        course=course,
                        student=student,
                        defaults={'status': 'active'}
                    )
                    
                    # Actualizar Student.course
                    from .models import Student
                    try:
                        student_profile = Student.objects.get(user=student)
                        if not student_profile.course:
                            student_profile.course = course
                            student_profile.save()
                    except Student.DoesNotExist:
                        pass
                    
                    messages.success(request, f'Estudiante "{student.get_full_name() or student.username}" matriculado exitosamente.')
                    return redirect('editor:tutor_course_roster', institution_slug=institution_slug, course_id=course_id)
            except User.DoesNotExist:
                messages.error(request, 'Estudiante no encontrado.')
        else:
            messages.error(request, 'Debes seleccionar un estudiante.')
    
    context = {
        'institution': institution,
        'course': course,
        'available_students': available_students,
    }
    return render(request, 'editor/academic/tutor/enroll_student.html', context)


# ============================================
# VISTAS DE ESTUDIANTE
# ============================================

@login_required
def student_courses_list(request, institution_slug):
    """Lista de cursos matriculados del estudiante"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution', 'student'], institution):
        messages.error(request, 'No tienes permisos para ver cursos.')
        return redirect('editor:dashboard')
    
    # Obtener cursos matriculados del estudiante
    courses = Course.objects.filter(
        institution=institution,
        enrollments__student=request.user,
        enrollments__status='active'
    ).annotate(
        tutors_count=Count('teaching_assignments', filter=Q(teaching_assignments__status='active'))
    ).distinct().order_by('-academic_year', 'name')
    
    context = {
        'institution': institution,
        'courses': courses,
        'user_role': UserRoleHelper.get_user_role(request.user, institution),
    }
    return render(request, 'editor/academic/student/courses_list.html', context)
