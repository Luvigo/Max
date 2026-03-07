"""
MÓDULO 3: Vistas de Tutor (solo lectura de perfil)

Regla: El admin gestiona tutores EXCLUSIVAMENTE desde Django Admin.
NO hay rutas/templates tipo /admin-panel/tutors.
El tutor solo tiene vista read-only de su perfil.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Institution, Membership, TutorProfile, StudentGroup
from .mixins import tutor_required


@login_required
@tutor_required
def tutor_profile(request, institution_slug):
    """
    Vista read-only del perfil del tutor.
    
    El tutor puede ver su información pero NO puede editarla.
    Para editar, debe contactar al administrador.
    """
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Verificar que el usuario es tutor de esta institución
    membership = Membership.objects.filter(
        user=request.user,
        institution=institution,
        role__in=['tutor', 'institution', 'admin'],
        is_active=True
    ).first()
    
    if not membership and not request.user.is_superuser:
        messages.error(request, 'No tienes acceso como tutor a esta institución.')
        return redirect('dashboard')
    
    # Obtener perfil de tutor (puede no existir si se creó solo con Membership)
    tutor_profile = TutorProfile.objects.filter(
        user=request.user,
        institution=institution
    ).first()
    
    # Obtener grupos del tutor
    my_groups = StudentGroup.objects.filter(
        institution=institution,
        tutor=request.user
    ).order_by('-academic_year', 'name')
    
    # Calcular estadísticas
    total_groups = my_groups.count()
    total_students = sum(g.get_students_count() for g in my_groups)
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'tutor_profile': tutor_profile,
        'membership': membership,
        'my_groups': my_groups,
        'stats': {
            'groups_count': total_groups,
            'students_count': total_students,
        }
    }
    
    return render(request, 'editor/tutor/profile.html', context)


@login_required
def check_tutor_status(request, institution_slug):
    """
    API para verificar si el tutor está activo.
    Usado para bloquear acciones si el tutor está inactivo.
    """
    from django.http import JsonResponse
    
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Verificar TutorProfile
    tutor_profile = TutorProfile.objects.filter(
        user=request.user,
        institution=institution
    ).first()
    
    if tutor_profile:
        if not tutor_profile.can_login():
            return JsonResponse({
                'ok': False,
                'active': False,
                'status': tutor_profile.status,
                'message': f'Tu cuenta de tutor está {tutor_profile.get_status_display()}. Contacta al administrador.'
            })
    
    # Verificar Membership
    membership = Membership.objects.filter(
        user=request.user,
        institution=institution,
        role='tutor'
    ).first()
    
    if membership and not membership.is_active:
        return JsonResponse({
            'ok': False,
            'active': False,
            'message': 'Tu membresía como tutor está inactiva. Contacta al administrador.'
        })
    
    return JsonResponse({
        'ok': True,
        'active': True,
        'status': tutor_profile.status if tutor_profile else 'active'
    })
