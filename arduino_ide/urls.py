"""
LIMPIEZA ARQUITECTÓNICA - URLs Principales

ROLES VÁLIDOS ÚNICOS:
- Admin: SOLO usa Django Admin (/admin/)
- Tutor: Dashboard y vistas en plataforma
- Estudiante: Dashboard y vistas en plataforma

❌ ELIMINADOS:
- /admin-panel/* (el admin usa /admin/)
- /dashboard/admin/ (el admin usa /admin/)
- institution_dashboard (institución es solo información)
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

from editor import dashboard_views
from editor import auth_views


# Vista helper para redirigir rutas obsoletas
def redirect_to_admin(request, *args, **kwargs):
    """Redirige rutas de admin-panel obsoletas a Django Admin"""
    return redirect('/admin/')


def redirect_to_dashboard(request, *args, **kwargs):
    """Redirige rutas de institution_dashboard al dashboard correcto"""
    return redirect('dashboard')


urlpatterns = [
    # ============================================
    # Django Admin - ÚNICO lugar para Administrador
    # ============================================
    path('admin/', admin.site.urls),
    
    # ============================================
    # Autenticación
    # ============================================
    path('login/', auth_views.user_login, name='login'),
    path('logout/', auth_views.user_logout, name='logout'),
    path('403/', auth_views.access_denied, name='access_denied'),
    
    # ============================================
    # Dashboard - Redirige según rol
    # ============================================
    path('dashboard/', dashboard_views.dashboard_redirect, name='dashboard'),
    path('select-institution/', dashboard_views.select_institution, name='select_institution'),
    
    # ============================================
    # ❌ RUTAS DEPRECADAS - Redirigen a /admin/ o dashboard
    # ============================================
    
    # Admin dashboard (DEPRECADO - admin usa /admin/)
    path('dashboard/admin/', redirect_to_admin, name='admin_dashboard'),
    
    # Admin panel routes (DEPRECADO - admin usa /admin/)
    path('admin-panel/', redirect_to_admin),
    path('admin-panel/<path:subpath>', redirect_to_admin),
    
    # Institution dashboard (DEPRECADO - institución no tiene cuenta)
    path('i/<slug:slug>/dashboard/', dashboard_views.institution_dashboard, name='institution_dashboard'),
    
    # ============================================
    # ✅ Dashboards válidos con tenant (institución)
    # ============================================
    path('i/<slug:slug>/dashboard/tutor/', dashboard_views.tutor_dashboard, name='tutor_dashboard'),
    path('i/<slug:slug>/dashboard/student/', dashboard_views.student_dashboard, name='student_dashboard'),
    
    # ============================================
    # Editor app - Rutas con tenant scoping
    # ============================================
    path('i/<slug:institution_slug>/', include('editor.urls')),
    
    # ============================================
    # Editor app - Rutas globales (IDE, APIs)
    # ============================================
    path('', include('editor.urls')),
]

# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None)
