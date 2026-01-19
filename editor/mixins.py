"""
Mixins y Decorators para RBAC y Tenant Scoping
"""
from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseForbidden, Http404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import View
from .models import Institution, Membership, UserRoleHelper


# ============================================
# DECORADORES PARA FUNCTION-BASED VIEWS
# ============================================

def login_required_with_institution(view_func):
    """
    Decorator que requiere login y verifica acceso a la institución actual.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión para acceder.')
            return redirect('login')
        
        # Si hay institución en URL, verificar acceso
        if request.current_institution and not request.current_membership:
            if not request.user.is_superuser:
                messages.error(request, 'No tienes acceso a esta institución.')
                return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    """
    Decorator que requiere uno de los roles especificados.
    
    Uso:
        @role_required('admin', 'institution')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Debes iniciar sesión para acceder.')
                return redirect('login')
            
            user_role = getattr(request, 'user_role', None)
            
            # Superuser siempre tiene acceso
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if user_role not in allowed_roles:
                messages.error(request, 'No tienes permisos para acceder a esta sección.')
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def institution_required(view_func):
    """
    Decorator que requiere una institución activa en el contexto.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión para acceder.')
            return redirect('login')
        
        if not request.current_institution:
            # Intentar redirect a institución única
            single_inst = UserRoleHelper.get_single_institution(request.user)
            if single_inst:
                # Reconstruir URL con institución
                new_path = f'/i/{single_inst.slug}{request.path}'
                return redirect(new_path)
            
            messages.info(request, 'Por favor selecciona una institución.')
            return redirect('select_institution')
        
        return view_func(request, *args, **kwargs)
    return wrapper


# ============================================
# MIXINS PARA CLASS-BASED VIEWS
# ============================================

class InstitutionContextMixin:
    """
    Mixin que añade contexto de institución a las vistas.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_institution'] = getattr(self.request, 'current_institution', None)
        context['current_membership'] = getattr(self.request, 'current_membership', None)
        context['user_role'] = getattr(self.request, 'user_role', None)
        context['user_institutions'] = getattr(self.request, 'user_institutions', [])
        return context


class InstitutionScopedMixin(LoginRequiredMixin, InstitutionContextMixin):
    """
    Mixin para vistas que requieren una institución activa.
    Filtra automáticamente querysets por institución.
    """
    login_url = '/login/'
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar autenticación
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Verificar institución
        if not request.current_institution:
            single_inst = UserRoleHelper.get_single_institution(request.user)
            if single_inst:
                new_path = f'/i/{single_inst.slug}{request.path}'
                return redirect(new_path)
            
            messages.info(request, 'Por favor selecciona una institución.')
            return redirect('select_institution')
        
        # Verificar acceso a la institución
        if not request.current_membership and not request.user.is_superuser:
            messages.error(request, 'No tienes acceso a esta institución.')
            return redirect('dashboard')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_institution(self):
        """Retorna la institución actual"""
        return self.request.current_institution
    
    def filter_by_institution(self, queryset):
        """Filtra un queryset por la institución actual"""
        institution = self.get_institution()
        if institution and hasattr(queryset.model, 'institution'):
            return queryset.filter(institution=institution)
        return queryset


class RoleRequiredMixin(UserPassesTestMixin):
    """
    Mixin que requiere roles específicos.
    
    Uso:
        class MyView(RoleRequiredMixin, TemplateView):
            allowed_roles = ['admin', 'institution']
    """
    allowed_roles = []
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        
        # Superuser siempre tiene acceso
        if self.request.user.is_superuser:
            return True
        
        user_role = getattr(self.request, 'user_role', None)
        return user_role in self.allowed_roles
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.warning(self.request, 'Debes iniciar sesión para acceder.')
            return redirect('login')
        
        messages.error(self.request, 'No tienes permisos para acceder a esta sección.')
        return redirect('dashboard')


class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin que requiere rol de administrador global"""
    allowed_roles = ['admin']


class InstitutionAdminRequiredMixin(RoleRequiredMixin):
    """Mixin que requiere rol de administrador de institución o superior"""
    allowed_roles = ['admin', 'institution']


class TutorRequiredMixin(RoleRequiredMixin):
    """Mixin que requiere rol de tutor o superior"""
    allowed_roles = ['admin', 'institution', 'tutor']


class StudentRequiredMixin(RoleRequiredMixin):
    """Mixin que acepta cualquier rol autenticado"""
    allowed_roles = ['admin', 'institution', 'tutor', 'student']


# ============================================
# HELPERS PARA TENANT-SAFE QUERIES
# ============================================

def get_object_for_institution_or_404(model, institution, **kwargs):
    """
    Obtener objeto verificando que pertenece a la institución.
    Lanza 404 si no existe o no pertenece a la institución (tenant-safe).
    """
    obj = get_object_or_404(model, **kwargs)
    
    # Verificar que el objeto pertenece a la institución
    if hasattr(obj, 'institution'):
        if obj.institution != institution:
            raise Http404("Objeto no encontrado")
    elif hasattr(obj, 'course') and obj.course:
        if obj.course.institution != institution:
            raise Http404("Objeto no encontrado")
    elif hasattr(obj, 'student') and obj.student and obj.student.course:
        if obj.student.course.institution != institution:
            raise Http404("Objeto no encontrado")
    
    return obj


def filter_queryset_by_institution(queryset, institution):
    """
    Filtra un queryset para que solo incluya objetos de la institución.
    Maneja diferentes tipos de modelos (con institution directa o anidada).
    """
    if not institution:
        return queryset.none()
    
    model = queryset.model
    
    if hasattr(model, 'institution'):
        return queryset.filter(institution=institution)
    elif hasattr(model, 'course'):
        return queryset.filter(course__institution=institution)
    elif hasattr(model, 'student'):
        return queryset.filter(student__course__institution=institution)
    
    return queryset
