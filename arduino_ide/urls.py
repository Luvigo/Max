"""
URL configuration for arduino_ide project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from editor import dashboard_views
from editor import agent_views
from editor import error_views

urlpatterns = [
    # Admin de Django
    path('admin/', admin.site.urls),
    
    # Autenticación global
    path('login/', auth_views.LoginView.as_view(template_name='editor/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard principal (redirige según rol)
    path('dashboard/', dashboard_views.dashboard_redirect, name='dashboard'),
    path('select-institution/', dashboard_views.select_institution, name='select_institution'),
    
    # Dashboards por rol
    path('dashboard/admin/', dashboard_views.admin_dashboard, name='admin_dashboard'),
    
    # Dashboards con tenant (institución)
    path('i/<slug:slug>/dashboard/', dashboard_views.institution_dashboard, name='institution_dashboard'),
    path('i/<slug:slug>/dashboard/tutor/', dashboard_views.tutor_dashboard, name='tutor_dashboard'),
    path('i/<slug:slug>/dashboard/student/', dashboard_views.student_dashboard, name='student_dashboard'),
    
    # Módulo 2: Estructura Académica con tenant scoping
    # Módulo 5: Agent Local Institucional con tenant scoping
    path('i/<slug:institution_slug>/', include('editor.urls')),
    
    # Editor app (incluye IDE y APIs) - rutas globales
    path('', include('editor.urls')),
    
    # Admin panel (global, sin tenant scoping)
    path('admin-panel/agents/', agent_views.admin_agents_list, name='admin_agents_list'),
    path('admin-panel/agents/<str:agent_id>/', agent_views.admin_agent_detail, name='admin_agent_detail'),
    
    # Módulo 6: Observabilidad (ErrorEvent/AuditLog) - Admin panel
    path('admin-panel/errors/', error_views.admin_errors_list, name='admin_errors_list'),
    path('admin-panel/errors/<str:error_id>/', error_views.admin_error_detail, name='admin_error_detail'),
]

# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None)
