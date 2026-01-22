"""
MÓDULO 2: Vistas de Institución (solo lectura)

Regla: NO hay vistas de admin para instituciones.
Solo vistas read-only para tutor y estudiante.
Todo CRUD de Institution vive en Django Admin (/admin/).
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Institution, Membership, Course, Enrollment, TeachingAssignment
from .mixins import tutor_required, student_required


@login_required
def my_institution(request, institution_slug):
    """
    Vista read-only de "Mi Institución" para cualquier rol.
    
    Muestra información general de la institución del usuario.
    NO permite edición - solo lectura.
    """
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Verificar que el usuario pertenece a la institución
    membership = Membership.objects.filter(
        user=request.user,
        institution=institution,
        is_active=True
    ).first()
    
    if not membership and not request.user.is_superuser:
        messages.error(request, 'No tienes acceso a esta institución.')
        return redirect('dashboard')
    
    # Determinar el rol del usuario
    user_role = membership.role if membership else 'admin'
    
    # Obtener estadísticas según el rol
    context = {
        'institution': institution,
        'user_role': user_role,
        'membership': membership,
    }
    
    # Estadísticas generales (visible para todos)
    context['stats'] = {
        'courses_count': institution.get_courses_count(),
        'tutors_count': institution.get_tutors_count(),
        'students_count': institution.get_students_count(),
    }
    
    # Si es tutor, mostrar sus cursos
    if user_role == 'tutor' or user_role in ['admin', 'institution']:
        context['my_courses'] = TeachingAssignment.objects.filter(
            tutor=request.user,
            course__institution=institution,
            status='active'
        ).select_related('course')
    
    # Si es estudiante, mostrar sus cursos
    if user_role == 'student':
        context['my_enrollments'] = Enrollment.objects.filter(
            student=request.user,
            course__institution=institution,
            status='active'
        ).select_related('course')
    
    return render(request, 'editor/institution/my_institution.html', context)


@login_required
@tutor_required
def tutor_my_institution(request, institution_slug):
    """
    Vista read-only de "Mi Institución" específica para tutores.
    """
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Verificar que el usuario es tutor de la institución
    membership = Membership.objects.filter(
        user=request.user,
        institution=institution,
        is_active=True,
        role__in=['tutor', 'institution', 'admin']
    ).first()
    
    if not membership and not request.user.is_superuser:
        messages.error(request, 'No tienes acceso como tutor a esta institución.')
        return redirect('dashboard')
    
    # Cursos del tutor
    my_courses = TeachingAssignment.objects.filter(
        tutor=request.user,
        course__institution=institution,
        status='active'
    ).select_related('course')
    
    # Calcular total de estudiantes en los cursos del tutor
    total_students = 0
    for assignment in my_courses:
        total_students += assignment.course.get_students_count()
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'my_courses': my_courses,
        'stats': {
            'courses_count': my_courses.count(),
            'students_count': total_students,
            'tutors_count': institution.get_tutors_count(),
            'total_students': institution.get_students_count(),
        }
    }
    
    return render(request, 'editor/institution/tutor_institution.html', context)


@login_required
@student_required
def student_my_institution(request, institution_slug):
    """
    Vista read-only de "Mi Institución" específica para estudiantes.
    """
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Verificar que el usuario pertenece a la institución
    membership = Membership.objects.filter(
        user=request.user,
        institution=institution,
        is_active=True
    ).first()
    
    if not membership and not request.user.is_superuser:
        messages.error(request, 'No tienes acceso a esta institución.')
        return redirect('dashboard')
    
    # Cursos del estudiante
    my_enrollments = Enrollment.objects.filter(
        student=request.user,
        course__institution=institution,
        status='active'
    ).select_related('course')
    
    # Tutores de mis cursos
    my_tutors = set()
    for enrollment in my_enrollments:
        for tutor in enrollment.course.get_assigned_tutors():
            my_tutors.add(tutor)
    
    context = {
        'institution': institution,
        'user_role': 'student',
        'my_enrollments': my_enrollments,
        'my_tutors': list(my_tutors),
        'stats': {
            'courses_count': my_enrollments.count(),
            'tutors_count': len(my_tutors),
        }
    }
    
    return render(request, 'editor/institution/student_institution.html', context)
