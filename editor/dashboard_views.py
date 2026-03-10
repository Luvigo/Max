"""
LIMPIEZA ARQUITECTÓNICA - Dashboards por Rol

ROLES VÁLIDOS ÚNICOS:
- Admin: SOLO usa Django Admin (/admin/)
- Tutor: Dashboard en plataforma
- Estudiante: Dashboard en plataforma

❌ ELIMINADOS:
- Dashboard de Admin (fuera de /admin/)
- Dashboard de Institución
- Rol "institution" como usuario
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    Institution, Membership, Course, Student, Project, StudentGroup,
    Activity, Submission, UserRoleHelper
)


@login_required
def dashboard_redirect(request):
    """
    Redirige al dashboard correspondiente según el rol del usuario.
    
    ROLES:
    - Admin/Superuser/Staff -> /admin/ (Django Admin)
    - Tutor -> /i/<slug>/dashboard/tutor/
    - Estudiante -> /i/<slug>/dashboard/student/
    
    ❌ NO existe dashboard de "institución" ni de "admin" en templates
    """
    user = request.user
    
    # Admin/Superuser/Staff -> Redirigir a Django Admin
    if user.is_superuser or user.is_staff:
        messages.info(request, 'Como administrador, usa Django Admin para gestionar el sistema.')
        return redirect('/admin/')
    
    # Obtener membresías activas del usuario
    memberships = Membership.objects.filter(
        user=user,
        is_active=True
    ).select_related('institution')
    
    if not memberships.exists():
        messages.warning(request, 'No tienes acceso a ninguna institución. Contacta a tu administrador.')
        return redirect('login')
    
    # Determinar rol principal (tutor tiene prioridad sobre estudiante)
    tutor_membership = memberships.filter(role='tutor').first()
    student_membership = memberships.filter(role='student').first()
    
    # Si es tutor
    if tutor_membership:
        return redirect('tutor_dashboard', slug=tutor_membership.institution.slug)
    
    # Si es estudiante
    if student_membership:
        return redirect('student_dashboard', slug=student_membership.institution.slug)
    
    # Rol "institution" obsoleto -> redirigir a admin si aplica
    institution_membership = memberships.filter(role='institution').first()
    if institution_membership:
        messages.warning(request, 'El rol de institución ha sido deprecado. Contacta al administrador.')
        return redirect('login')
    
    # Fallback
    messages.warning(request, 'No tienes un rol válido asignado.')
    return redirect('login')


@login_required
def select_institution(request):
    """
    Vista para seleccionar institución cuando el usuario tiene múltiples.
    Solo aplica para Tutores y Estudiantes.
    """
    user = request.user
    
    # Admin va a /admin/
    if user.is_superuser or user.is_staff:
        return redirect('/admin/')
    
    # Obtener membresías válidas (solo tutor/student)
    memberships = Membership.objects.filter(
        user=user,
        is_active=True,
        role__in=['tutor', 'student']
    ).select_related('institution')
    
    if not memberships.exists():
        messages.warning(request, 'No tienes acceso a ninguna institución.')
        return redirect('login')
    
    if memberships.count() == 1:
        m = memberships.first()
        if m.role == 'tutor':
            return redirect('tutor_dashboard', slug=m.institution.slug)
        else:
            return redirect('student_dashboard', slug=m.institution.slug)
    
    context = {
        'memberships': memberships,
        'page_title': 'Seleccionar Institución',
    }
    return render(request, 'dashboards/select_institution.html', context)


# ============================================
# ❌ ELIMINADO: admin_dashboard
# El Admin usa EXCLUSIVAMENTE Django Admin (/admin/)
# ============================================

def admin_dashboard(request):
    """
    DEPRECATED: El admin usa Django Admin.
    Esta vista redirige a /admin/
    """
    return redirect('/admin/')


# ============================================
# ❌ ELIMINADO: institution_dashboard  
# La institución es SOLO información, no tiene cuenta/login/dashboard
# ============================================

def institution_dashboard(request, slug):
    """
    DEPRECATED: No existe dashboard de institución.
    Redirige según el rol real del usuario.
    """
    user = request.user
    
    if not user.is_authenticated:
        return redirect('login')
    
    if user.is_superuser or user.is_staff:
        return redirect('/admin/')
    
    # Verificar membresía real
    membership = Membership.objects.filter(
        user=user,
        institution__slug=slug,
        is_active=True
    ).first()
    
    if not membership:
        messages.error(request, 'No tienes acceso a esta institución.')
        return redirect('dashboard')
    
    # Redirigir según rol real
    if membership.role == 'tutor':
        return redirect('tutor_dashboard', slug=slug)
    elif membership.role == 'student':
        return redirect('student_dashboard', slug=slug)
    elif membership.role == 'institution':
        # Rol deprecado
        messages.warning(request, 'El rol de institución ha sido deprecado.')
        return redirect('login')
    else:
        return redirect('dashboard')


# ============================================
# ✅ TUTOR DASHBOARD
# ============================================

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
    
    user = request.user
    
    # Superuser puede ver cualquier institución
    if not user.is_superuser:
        membership = Membership.objects.filter(
            user=user,
            institution=institution,
            is_active=True,
            role='tutor'
        ).first()
        
        if not membership:
            # Verificar si tiene otro rol
            other_membership = Membership.objects.filter(
                user=user,
                institution=institution,
                is_active=True
            ).first()
            
            if other_membership and other_membership.role == 'student':
                return redirect('student_dashboard', slug=slug)
            
            messages.error(request, 'No tienes acceso como tutor a esta institución.')
            return redirect('dashboard')
    
    # Grupos del tutor
    my_groups = StudentGroup.objects.filter(
        institution=institution,
        tutor=user,
        status='active'
    ).annotate(
        students_count=Count('students', filter=Q(students__is_active=True))
    )
    
    # Total estudiantes en mis grupos
    total_students = Student.objects.filter(
        group__in=my_groups,
        is_active=True
    ).count()
    
    # Actividades del tutor
    my_activities = Activity.objects.filter(
        Q(group__tutor=user) | Q(created_by=user),
        Q(group__institution=institution) | Q(course__institution=institution)
    ).order_by('-created_at')
    
    total_activities = my_activities.count()
    
    # Entregas pendientes de calificar
    pending_submissions = Submission.objects.filter(
        activity__in=my_activities,
        status='submitted'
    ).count()
    
    # Actividad reciente
    recent_submissions = Submission.objects.filter(
        activity__in=my_activities,
        status__in=['submitted', 'graded']
    ).select_related('student', 'activity').order_by('-submitted_at')[:10]
    
    # Estudiantes recientes
    recent_students = Student.objects.filter(
        group__in=my_groups,
        is_active=True
    ).select_related('user', 'group').order_by('-created_at')[:5]
    
    context = {
        'page_title': f'Dashboard Tutor - {institution.name}',
        'user_role': 'tutor',
        'institution': institution,
        'metrics': {
            'groups': my_groups.count(),
            'students': total_students,
            'activities': total_activities,
            'pending': pending_submissions,
        },
        'my_groups': my_groups,
        'recent_submissions': recent_submissions,
        'recent_students': recent_students,
    }
    return render(request, 'dashboards/tutor_dashboard.html', context)


# ============================================
# ✅ STUDENT DASHBOARD
# ============================================

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
    
    user = request.user
    
    # Verificar acceso
    if not user.is_superuser:
        membership = Membership.objects.filter(
            user=user,
            institution=institution,
            is_active=True,
            role='student'
        ).first()
        
        if not membership:
            # Verificar si tiene otro rol
            other_membership = Membership.objects.filter(
                user=user,
                institution=institution,
                is_active=True
            ).first()
            
            if other_membership and other_membership.role == 'tutor':
                return redirect('tutor_dashboard', slug=slug)
            
            messages.error(request, 'No tienes acceso como estudiante a esta institución.')
            return redirect('dashboard')
    
    # Obtener perfil de estudiante
    try:
        student = Student.objects.get(user=user, institution=institution, is_active=True)
    except Student.DoesNotExist:
        try:
            student = Student.objects.get(user=user, is_active=True)
        except Student.DoesNotExist:
            student = None
    
    # Grupo del estudiante
    my_group = student.group if student else None
    my_tutor = my_group.tutor if my_group else None
    
    # Actividades del grupo
    if my_group:
        my_activities = Activity.objects.filter(
            group=my_group,
            status='published'
        ).order_by('-deadline', '-created_at')
        
        # Entregas del estudiante
        my_submissions = Submission.objects.filter(
            student=user,
            activity__group=my_group
        ).select_related('activity')
        
        # Actividades pendientes
        submitted_activity_ids = my_submissions.filter(
            status__in=['submitted', 'graded']
        ).values_list('activity_id', flat=True)
        
        pending_activities = my_activities.exclude(id__in=submitted_activity_ids).count()
        
        # Calificaciones
        graded_submissions = my_submissions.filter(status='graded', score__isnull=False)
        total_graded = graded_submissions.count()
        
    else:
        my_activities = Activity.objects.none()
        my_submissions = Submission.objects.none()
        pending_activities = 0
        graded_submissions = Submission.objects.none()
        total_graded = 0
    
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
    
    context = {
        'page_title': f'Mi Dashboard - {institution.name}',
        'user_role': 'student',
        'institution': institution,
        'student': student,
        'my_group': my_group,
        'my_tutor': my_tutor,
        'metrics': {
            'activities': my_activities.count() if my_group else 0,
            'pending': pending_activities,
            'graded': total_graded,
            'projects': total_projects,
        },
        'recent_projects': recent_projects,
        'my_activities': my_activities[:5] if my_group else [],
    }
    return render(request, 'dashboards/student_dashboard.html', context)
