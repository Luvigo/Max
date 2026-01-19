"""
Vistas de Dashboards por Rol
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import (
    Institution, Membership, Course, Student, Project, 
    UserRoleHelper
)
from .mixins import (
    role_required, institution_required, login_required_with_institution,
    InstitutionScopedMixin, AdminRequiredMixin, InstitutionAdminRequiredMixin,
    TutorRequiredMixin
)


@login_required
def dashboard_redirect(request):
    """
    Redirige al dashboard correspondiente según el rol del usuario.
    """
    user = request.user
    
    # Superuser va al dashboard admin
    if user.is_superuser:
        return redirect('admin_dashboard')
    
    # Obtener rol del usuario
    role = UserRoleHelper.get_user_role(user)
    
    if role == 'admin':
        return redirect('admin_dashboard')
    
    # Para otros roles, necesitamos una institución
    institutions = UserRoleHelper.get_user_institutions(user)
    
    if not institutions.exists():
        messages.warning(request, 'No tienes acceso a ninguna institución.')
        return redirect('login')
    
    # Si solo tiene una institución, redirigir directamente
    if institutions.count() == 1:
        inst = institutions.first()
        if role == 'institution':
            return redirect('institution_dashboard', slug=inst.slug)
        elif role == 'tutor':
            return redirect('tutor_dashboard', slug=inst.slug)
        else:  # student
            return redirect('student_dashboard', slug=inst.slug)
    
    # Múltiples instituciones - mostrar selector
    return redirect('select_institution')


@login_required
def select_institution(request):
    """
    Vista para seleccionar institución cuando el usuario tiene múltiples.
    """
    institutions = UserRoleHelper.get_user_institutions(request.user)
    
    if not institutions.exists():
        messages.warning(request, 'No tienes acceso a ninguna institución.')
        return redirect('login')
    
    if institutions.count() == 1:
        inst = institutions.first()
        return redirect('institution_dashboard', slug=inst.slug)
    
    # Obtener membresías para mostrar roles
    memberships = Membership.objects.filter(
        user=request.user,
        institution__in=institutions,
        is_active=True
    ).select_related('institution')
    
    context = {
        'memberships': memberships,
        'page_title': 'Seleccionar Institución',
    }
    return render(request, 'dashboards/select_institution.html', context)


@login_required
@role_required('admin')
def admin_dashboard(request):
    """
    Dashboard para administradores globales.
    Muestra métricas de todas las instituciones.
    """
    # Métricas globales
    total_institutions = Institution.objects.filter(status='active').count()
    total_users = Membership.objects.filter(is_active=True).values('user').distinct().count()
    total_courses = Course.objects.filter(is_active=True).count()
    total_students = Student.objects.filter(is_active=True).count()
    total_projects = Project.objects.filter(is_active=True).count()
    
    # Instituciones recientes
    recent_institutions = Institution.objects.filter(
        status='active'
    ).order_by('-created_at')[:5]
    
    # Actividad reciente (proyectos)
    recent_activity = Project.objects.filter(
        is_active=True
    ).select_related(
        'student__user', 'student__course__institution'
    ).order_by('-updated_at')[:10]
    
    # Estadísticas por institución
    institutions_stats = Institution.objects.filter(
        status='active'
    ).annotate(
        members_count=Count('memberships', filter=models.Q(memberships__is_active=True)),
        courses_count=Count('courses', filter=models.Q(courses__is_active=True))
    ).order_by('-members_count')[:10]
    
    context = {
        'page_title': 'Dashboard Administrador',
        'user_role': 'admin',
        'metrics': {
            'institutions': total_institutions,
            'users': total_users,
            'courses': total_courses,
            'students': total_students,
            'projects': total_projects,
        },
        'recent_institutions': recent_institutions,
        'recent_activity': recent_activity,
        'institutions_stats': institutions_stats,
    }
    return render(request, 'dashboards/admin_dashboard.html', context)


@login_required
def institution_dashboard(request, slug):
    """
    Dashboard para administradores de institución.
    """
    try:
        institution = Institution.objects.get(slug=slug, status='active')
    except Institution.DoesNotExist:
        messages.error(request, 'Institución no encontrada.')
        return redirect('dashboard')
    
    # Verificar acceso
    if not request.user.is_superuser:
        membership = Membership.objects.filter(
            user=request.user,
            institution=institution,
            is_active=True,
            role__in=['admin', 'institution']
        ).first()
        
        if not membership:
            # Verificar si tiene otro rol
            other_membership = Membership.objects.filter(
                user=request.user,
                institution=institution,
                is_active=True
            ).first()
            
            if other_membership:
                if other_membership.role == 'tutor':
                    return redirect('tutor_dashboard', slug=slug)
                else:
                    return redirect('student_dashboard', slug=slug)
            
            messages.error(request, 'No tienes acceso a esta institución.')
            return redirect('dashboard')
    
    # Métricas de la institución
    total_members = Membership.objects.filter(institution=institution, is_active=True).count()
    total_courses = Course.objects.filter(institution=institution, is_active=True).count()
    total_students = Student.objects.filter(course__institution=institution, is_active=True).count()
    total_projects = Project.objects.filter(
        student__course__institution=institution, is_active=True
    ).count()
    
    # Cursos
    courses = Course.objects.filter(
        institution=institution, is_active=True
    ).annotate(
        students_count=Count('students', filter=models.Q(students__is_active=True))
    ).order_by('-created_at')[:5]
    
    # Actividad reciente
    recent_activity = Project.objects.filter(
        student__course__institution=institution,
        is_active=True
    ).select_related('student__user', 'student__course').order_by('-updated_at')[:10]
    
    # Membresías por rol
    memberships_by_role = Membership.objects.filter(
        institution=institution, is_active=True
    ).values('role').annotate(count=Count('id'))
    
    context = {
        'page_title': f'Dashboard - {institution.name}',
        'user_role': 'institution',
        'institution': institution,
        'metrics': {
            'members': total_members,
            'courses': total_courses,
            'students': total_students,
            'projects': total_projects,
        },
        'courses': courses,
        'recent_activity': recent_activity,
        'memberships_by_role': memberships_by_role,
    }
    return render(request, 'dashboards/institution_dashboard.html', context)


@login_required
def tutor_dashboard(request, slug):
    """
    Dashboard para tutores.
    """
    try:
        institution = Institution.objects.get(slug=slug, status='active')
    except Institution.DoesNotExist:
        messages.error(request, 'Institución no encontrada.')
        return redirect('dashboard')
    
    # Verificar acceso
    if not request.user.is_superuser:
        membership = Membership.objects.filter(
            user=request.user,
            institution=institution,
            is_active=True,
            role__in=['admin', 'institution', 'tutor']
        ).first()
        
        if not membership:
            messages.error(request, 'No tienes acceso como tutor a esta institución.')
            return redirect('dashboard')
    
    # Cursos del tutor
    my_courses = Course.objects.filter(
        institution=institution,
        tutor=request.user,
        is_active=True
    ).annotate(
        students_count=Count('students', filter=models.Q(students__is_active=True))
    )
    
    # Total estudiantes en mis cursos
    total_students = Student.objects.filter(
        course__in=my_courses,
        is_active=True
    ).count()
    
    # Total proyectos de mis estudiantes
    total_projects = Project.objects.filter(
        student__course__in=my_courses,
        is_active=True
    ).count()
    
    # Actividad reciente de mis estudiantes
    recent_activity = Project.objects.filter(
        student__course__in=my_courses,
        is_active=True
    ).select_related('student__user', 'student__course').order_by('-updated_at')[:10]
    
    # Estudiantes recientes
    recent_students = Student.objects.filter(
        course__in=my_courses,
        is_active=True
    ).select_related('user', 'course').order_by('-created_at')[:5]
    
    context = {
        'page_title': f'Dashboard Tutor - {institution.name}',
        'user_role': 'tutor',
        'institution': institution,
        'metrics': {
            'courses': my_courses.count(),
            'students': total_students,
            'projects': total_projects,
        },
        'my_courses': my_courses,
        'recent_activity': recent_activity,
        'recent_students': recent_students,
    }
    return render(request, 'dashboards/tutor_dashboard.html', context)


@login_required
def student_dashboard(request, slug):
    """
    Dashboard para estudiantes.
    """
    try:
        institution = Institution.objects.get(slug=slug, status='active')
    except Institution.DoesNotExist:
        messages.error(request, 'Institución no encontrada.')
        return redirect('dashboard')
    
    # Verificar acceso
    if not request.user.is_superuser:
        membership = Membership.objects.filter(
            user=request.user,
            institution=institution,
            is_active=True
        ).first()
        
        if not membership:
            messages.error(request, 'No tienes acceso a esta institución.')
            return redirect('dashboard')
    
    # Obtener perfil de estudiante
    try:
        student = Student.objects.get(user=request.user, is_active=True)
    except Student.DoesNotExist:
        student = None
    
    # Proyectos del estudiante
    if student:
        my_projects = Project.objects.filter(
            student=student,
            is_active=True
        ).order_by('-updated_at')
        total_projects = my_projects.count()
        recent_projects = my_projects[:5]
    else:
        my_projects = Project.objects.none()
        total_projects = 0
        recent_projects = []
    
    # Curso actual
    current_course = student.course if student else None
    
    context = {
        'page_title': f'Mi Dashboard - {institution.name}',
        'user_role': 'student',
        'institution': institution,
        'student': student,
        'current_course': current_course,
        'metrics': {
            'projects': total_projects,
        },
        'recent_projects': recent_projects,
    }
    return render(request, 'dashboards/student_dashboard.html', context)


# Necesitamos importar models para los filtros
from django.db import models
