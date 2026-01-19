"""
Vistas de autenticación personalizadas
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.http import require_http_methods


def student_login(request):
    """Página de login para estudiantes"""
    # Solo permitir GET y POST
    if request.method not in ['GET', 'POST']:
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['GET', 'POST'])
    
    # Si el usuario ya está autenticado y NO viene de un POST (es decir, ya está logueado)
    # solo redirigir si NO es una petición POST (para permitir logout y re-login)
    if request.user.is_authenticated and request.method != 'POST':
        # Si ya está autenticado, redirigir según su tipo
        from .models import Student
        try:
            student = Student.objects.get(user=request.user, is_active=True)
            # Redirigir al dashboard de estudiante
            return redirect('editor:student_dashboard')
        except Student.DoesNotExist:
            # No es estudiante, verificar si es admin
            if request.user.is_staff or request.user.is_superuser:
                return redirect('editor:admin_dashboard')
            # Si no es ni estudiante ni admin, ir al editor
            return redirect('editor:index')
        except Exception as e:
            # Error al verificar, ir al editor por defecto
            return redirect('editor:index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido, {user.get_full_name() or user.username}!')
                
                # Redirigir según el tipo de usuario
                # Primero verificar si es estudiante (tiene perfil de estudiante)
                from .models import Student
                try:
                    student = Student.objects.get(user=user, is_active=True)
                    # Si tiene perfil de estudiante activo, redirigir al dashboard de estudiante
                    return redirect('editor:student_dashboard')
                except Student.DoesNotExist:
                    # No es estudiante, verificar si es admin
                    pass
                except Exception:
                    # Error al verificar, continuar con la lógica normal
                    pass
                
                # Solo si NO es estudiante, verificar si es admin
                if user.is_staff or user.is_superuser:
                    return redirect('editor:admin_dashboard')
                
                return redirect('editor:index')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos')
        else:
            messages.error(request, 'Por favor, completa todos los campos')
    
    return render(request, 'editor/login.html')


@require_http_methods(["GET", "POST"])
def admin_login(request):
    """Página de login para administradores (redirige al admin de Django)"""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('editor:admin_dashboard')
        else:
            return redirect('editor:student_dashboard')
    
    # Redirigir al login del admin de Django
    return redirect('/admin/login/')

