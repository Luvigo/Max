"""
MÓDULO 2: Vistas de Institución (solo lectura)

Regla: NO hay vistas de admin para instituciones.
Solo vistas read-only para tutor y estudiante.
Todo CRUD de Institution vive en Django Admin (/admin/).
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.db.models import Q
from .models import Institution, Membership, StudentGroup, Student
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
        'groups_count': StudentGroup.objects.filter(institution=institution, status='active').count(),
        'tutors_count': institution.get_tutors_count(),
        'students_count': institution.get_students_count(),
    }
    
    # Si es tutor, mostrar sus grupos
    if user_role == 'tutor' or user_role in ['admin', 'institution']:
        context['my_groups'] = StudentGroup.objects.filter(
            institution=institution,
            tutor=request.user
        ).order_by('-academic_year', 'name')
    
    # Si es estudiante, mostrar su grupo
    if user_role == 'student':
        student_profile = Student.objects.filter(
            user=request.user,
            institution=institution,
            is_active=True
        ).select_related('group').first()
        context['my_group'] = student_profile.group if student_profile else None
    
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
    
    # Grupos del tutor
    my_groups = StudentGroup.objects.filter(
        institution=institution,
        tutor=request.user
    ).order_by('-academic_year', 'name')
    
    # Calcular total de estudiantes en los grupos del tutor
    total_students = sum(g.get_students_count() for g in my_groups)
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'my_groups': my_groups,
        'stats': {
            'groups_count': my_groups.count(),
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
    
    # Grupo del estudiante
    student_profile = Student.objects.filter(
        user=request.user,
        institution=institution,
        is_active=True
    ).select_related('group', 'tutor').first()
    
    my_group = student_profile.group if student_profile else None
    my_tutor = student_profile.tutor if student_profile else None
    
    context = {
        'institution': institution,
        'user_role': 'student',
        'my_group': my_group,
        'my_tutor': my_tutor,
        'stats': {
            'groups_count': 1 if my_group else 0,
            'tutors_count': 1 if my_tutor else 0,
        }
    }
    
    return render(request, 'editor/institution/student_institution.html', context)
