"""
MÓDULO 1: Vistas de autenticación
Auth + Roles (Admin, Tutor, Estudiante)

Reglas:
- Admin usa SOLO Django Admin (/admin/)
- Tutor -> /i/<slug>/tutor/
- Estudiante -> /i/<slug>/student/
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .models import UserRoleHelper, Membership


def get_post_login_redirect(user):
    """
    Determina la URL de redirección según el rol del usuario.
    
    Returns:
        tuple: (url, role_name) o (None, None) si no tiene rol
    """
    # Admin/Staff -> Django Admin
    if user.is_superuser or user.is_staff:
        return '/admin/', 'admin'
    
    # Obtener rol y primera institución
    role = UserRoleHelper.get_user_role(user)
    institutions = UserRoleHelper.get_user_institutions(user)
    
    if not institutions.exists():
        return None, None
    
    # Si tiene una sola institución, redirigir directamente
    if institutions.count() == 1:
        inst = institutions.first()
        
        if role == 'institution':
            return f'/i/{inst.slug}/dashboard/', 'institution'
        elif role == 'tutor':
            return f'/i/{inst.slug}/dashboard/tutor/', 'tutor'
        elif role == 'student':
            return f'/i/{inst.slug}/dashboard/student/', 'student'
    
    # Múltiples instituciones -> selector
    return 'select_institution', role


def user_login(request):
    """
    Página de login principal para usuarios normales (estudiantes, tutores, instituciones).
    Los administradores deben usar /admin/login/
    
    Flujo post-login:
    - Admin -> /admin/
    - Tutor -> /i/<slug>/dashboard/tutor/
    - Estudiante -> /i/<slug>/dashboard/student/
    """
    # Si ya está autenticado, redirigir según rol
    if request.user.is_authenticated:
        redirect_url, role = get_post_login_redirect(request.user)
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
        
        # Verificar si es admin/staff - redirigir al login de admin
        if user.is_superuser or user.is_staff:
            messages.info(request, 'Los administradores deben usar el panel de administración.')
            return redirect('/admin/login/')
        
        # Usuario normal - hacer login
        login(request, user)
        
        # Obtener nombre para el mensaje de bienvenida
        display_name = user.get_full_name() or user.username
        role = UserRoleHelper.get_user_role(user)
        role_display = {
            'institution': 'Administrador de Institución',
            'tutor': 'Tutor',
            'student': 'Estudiante'
        }.get(role, 'Usuario')
        
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
        
        # Fallback: dashboard general
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
    
    # Redirigir al login del admin de Django
    return redirect('/admin/login/')


def access_denied(request):
    """
    Vista para mostrar página de acceso denegado (403).
    """
    return render(request, 'editor/403.html', status=403)
