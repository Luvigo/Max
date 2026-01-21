"""
Vistas de autenticación personalizadas
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .models import UserRoleHelper


def user_login(request):
    """
    Página de login principal para usuarios normales (estudiantes, tutores, instituciones).
    Los administradores deben usar /admin/login/
    """
    # Si ya está autenticado, redirigir según rol
    if request.user.is_authenticated:
        # Si es admin, redirigir al admin de Django
        if request.user.is_superuser or request.user.is_staff:
            return redirect('/admin/')
        # Otros usuarios van al dashboard
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Por favor, completa todos los campos.')
            return render(request, 'editor/login.html')
        
        # Autenticar usuario
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            messages.error(request, 'Usuario o contraseña incorrectos.')
            return render(request, 'editor/login.html')
        
        # Verificar si es admin/staff - redirigir al login de admin
        if user.is_superuser or user.is_staff:
            messages.info(request, 'Los administradores deben usar el panel de administración.')
            return redirect('/admin/login/')
        
        # Usuario normal - hacer login y redirigir al dashboard
        login(request, user)
        
        # Obtener nombre para el mensaje de bienvenida
        display_name = user.get_full_name() or user.username
        messages.success(request, f'¡Bienvenido, {display_name}!')
        
        # Redirigir al dashboard (que a su vez redirige según el rol)
        next_url = request.GET.get('next') or request.POST.get('next')
        if next_url:
            return redirect(next_url)
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
    """Redirige al login del admin de Django"""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('/admin/')
        else:
            return redirect('dashboard')
    
    # Redirigir al login del admin de Django
    return redirect('/admin/login/')
