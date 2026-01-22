"""
LIMPIEZA ARQUITECTÓNICA - Autenticación

ROLES VÁLIDOS ÚNICOS:
- Admin: SOLO usa Django Admin (/admin/)
- Tutor: Dashboard y vistas en plataforma
- Estudiante: Dashboard y vistas en plataforma

❌ ELIMINADOS:
- Rol "institution" - La institución es solo información
- Dashboard de admin fuera de /admin/
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .models import UserRoleHelper, Membership


def get_post_login_redirect(user):
    """
    Determina la URL de redirección según el rol del usuario.
    
    ROLES:
    - Admin/Staff -> /admin/
    - Tutor -> /i/<slug>/dashboard/tutor/
    - Estudiante -> /i/<slug>/dashboard/student/
    
    ❌ ELIMINADO: Rol "institution"
    
    Returns:
        tuple: (url, role_name) o (None, None) si no tiene rol válido
    """
    # Admin/Staff -> Django Admin
    if user.is_superuser or user.is_staff:
        return '/admin/', 'admin'
    
    # Obtener membresías válidas (solo tutor o student)
    memberships = Membership.objects.filter(
        user=user,
        is_active=True,
        role__in=['tutor', 'student']
    ).select_related('institution')
    
    if not memberships.exists():
        # Verificar si tiene rol "institution" deprecado
        old_membership = Membership.objects.filter(
            user=user,
            is_active=True,
            role='institution'
        ).first()
        if old_membership:
            return None, 'institution_deprecated'
        return None, None
    
    # Priorizar tutor sobre estudiante
    tutor_membership = memberships.filter(role='tutor').first()
    student_membership = memberships.filter(role='student').first()
    
    if memberships.count() == 1:
        m = memberships.first()
        if m.role == 'tutor':
            return f'/i/{m.institution.slug}/dashboard/tutor/', 'tutor'
        else:
            return f'/i/{m.institution.slug}/dashboard/student/', 'student'
    
    # Múltiples instituciones -> selector
    return 'select_institution', tutor_membership.role if tutor_membership else student_membership.role


def user_login(request):
    """
    Página de login principal para Tutores y Estudiantes.
    
    FLUJO:
    - Admin/Staff -> Redirigir a /admin/login/
    - Tutor -> /i/<slug>/dashboard/tutor/
    - Estudiante -> /i/<slug>/dashboard/student/
    
    ❌ Rol "institution" DEPRECADO
    """
    # Si ya está autenticado, redirigir según rol
    if request.user.is_authenticated:
        user = request.user
        
        # Admin va al admin
        if user.is_superuser or user.is_staff:
            return redirect('/admin/')
        
        redirect_url, role = get_post_login_redirect(user)
        
        if role == 'institution_deprecated':
            messages.warning(request, 'Tu rol de "institución" ha sido deprecado. Contacta al administrador.')
            logout(request)
            return render(request, 'editor/login.html')
        
        if redirect_url:
            if redirect_url == 'select_institution':
                return redirect('select_institution')
            return redirect(redirect_url)
        
        return redirect('editor:index')  # Fallback al IDE
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Por favor, completa todos los campos.')
            return render(request, 'editor/login.html')
        
        # Autenticar usuario
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            messages.error(request, 'Por favor, introduzca un nombre de usuario y clave correctos. Observe que ambos campos pueden ser sensibles a mayúsculas.')
            return render(request, 'editor/login.html')
        
        # Admin/Staff -> Redirigir a login de admin
        if user.is_superuser or user.is_staff:
            messages.info(request, 'Los administradores deben usar el panel de administración.')
            return redirect('/admin/login/')
        
        # Verificar que tiene rol válido (tutor o student)
        valid_membership = Membership.objects.filter(
            user=user,
            is_active=True,
            role__in=['tutor', 'student']
        ).exists()
        
        if not valid_membership:
            # Verificar si tiene rol deprecado
            old_membership = Membership.objects.filter(
                user=user,
                is_active=True,
                role='institution'
            ).exists()
            
            if old_membership:
                messages.error(request, 'Tu rol de "institución" ha sido deprecado. Contacta al administrador para obtener acceso como Tutor o Estudiante.')
                return render(request, 'editor/login.html')
            
            messages.error(request, 'No tienes un rol válido asignado. Contacta al administrador.')
            return render(request, 'editor/login.html')
        
        # Login exitoso
        login(request, user)
        
        # Mensaje de bienvenida
        display_name = user.get_full_name() or user.username
        membership = Membership.objects.filter(
            user=user,
            is_active=True,
            role__in=['tutor', 'student']
        ).first()
        
        role_display = 'Tutor' if membership and membership.role == 'tutor' else 'Estudiante'
        messages.success(request, f'¡Bienvenido, {display_name}! ({role_display})')
        
        # Redirigir según next_url o rol
        next_url = request.GET.get('next') or request.POST.get('next')
        if next_url and not next_url.startswith('/admin'):
            return redirect(next_url)
        
        # Redirigir según rol
        redirect_url, _ = get_post_login_redirect(user)
        if redirect_url:
            if redirect_url == 'select_institution':
                return redirect('select_institution')
            return redirect(redirect_url)
        
        return redirect('dashboard')
    
    # GET - mostrar formulario
    return render(request, 'editor/login.html')


def user_logout(request):
    """Cerrar sesión"""
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


@require_http_methods(["GET", "POST"])
def admin_login(request):
    """
    Redirige al login del admin de Django.
    Los administradores NO usan templates personalizados.
    """
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('/admin/')
        else:
            return redirect('dashboard')
    
    return redirect('/admin/login/')


def access_denied(request):
    """
    Vista para mostrar página de acceso denegado (403).
    """
    return render(request, 'editor/403.html', status=403)
