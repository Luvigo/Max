"""
Middleware para Multi-tenant y RBAC
"""
from django.shortcuts import redirect
from django.http import Http404
from django.contrib import messages
from .models import Institution, Membership, UserRoleHelper


class TenantMiddleware:
    """
    Middleware para resolver el tenant (institución) desde la URL.
    
    URLs con formato: /i/<slug>/...
    
    Atributos añadidos al request:
    - request.current_institution: Institution actual o None
    - request.current_membership: Membership del usuario en la institución o None
    - request.user_role: Rol del usuario (admin, institution, tutor, student)
    - request.user_institutions: QuerySet de instituciones del usuario
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Inicializar atributos
        request.current_institution = None
        request.current_membership = None
        request.user_role = None
        request.user_institutions = Institution.objects.none()
        
        # Obtener instituciones del usuario si está autenticado
        if request.user.is_authenticated:
            request.user_institutions = UserRoleHelper.get_user_institutions(request.user)
            request.user_role = UserRoleHelper.get_user_role(request.user)
        
        # Resolver tenant desde URL
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) >= 2 and path_parts[0] == 'i':
            slug = path_parts[1]
            try:
                institution = Institution.objects.get(slug=slug, status='active')
                request.current_institution = institution
                
                # Obtener membership si el usuario está autenticado
                if request.user.is_authenticated:
                    # Superuser tiene acceso a todo
                    if request.user.is_superuser:
                        request.user_role = 'admin'
                    else:
                        membership = Membership.objects.filter(
                            user=request.user,
                            institution=institution,
                            is_active=True
                        ).first()
                        
                        if membership:
                            request.current_membership = membership
                            request.user_role = membership.role
                        else:
                            # Usuario no tiene acceso a esta institución
                            request.current_institution = None
                            
            except Institution.DoesNotExist:
                # Institución no encontrada - se manejará en la vista
                pass
        
        response = self.get_response(request)
        return response


def get_current_institution(request):
    """Helper function para obtener la institución actual del request"""
    return getattr(request, 'current_institution', None)


def get_current_membership(request):
    """Helper function para obtener la membresía actual del request"""
    return getattr(request, 'current_membership', None)


def get_user_role(request):
    """Helper function para obtener el rol del usuario"""
    return getattr(request, 'user_role', None)
