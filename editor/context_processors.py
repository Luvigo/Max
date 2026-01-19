"""
Context Processors para MAX-IDE
Añade variables globales a todos los templates
"""
from django.conf import settings


def global_context(request):
    """
    Añade variables globales a todos los templates
    """
    context = {
        # Build ID para cache-busting de assets
        'BUILD_ID': getattr(settings, 'BUILD_ID', 'dev'),
        
        # DEBUG mode
        'DEBUG': settings.DEBUG,
        
        # Información del tenant/institución
        'current_institution': getattr(request, 'current_institution', None),
        'current_membership': getattr(request, 'current_membership', None),
        'user_role': getattr(request, 'user_role', None),
        'user_institutions': getattr(request, 'user_institutions', []),
        
        # Alias para templates
        'institution': getattr(request, 'current_institution', None),
    }
    
    return context
