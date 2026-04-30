"""
URLs globales de Editor - Rutas que NO requieren institution_slug.

Incluidas en la raíz (path '') para IDE, APIs, etc.
SIN app_name: evita urls.W005 (namespace 'editor' duplicado).
El namespace 'editor' pertenece solo a editor.urls (tenant bajo i/<slug>/).
"""
from django.urls import path
from django.shortcuts import redirect
from . import views
from . import ide_views
from . import agent_views
from . import error_views
from . import notification_views
from . import student_views

# Sin app_name: estas URLs quedan sin namespace en la raíz.
# reverse('index'), reverse('compile'), etc. apuntan aquí.


def deprecated_redirect(request, *args, **kwargs):
    return redirect('dashboard')


def root_redirect(request):
    """
    La URL principal (/) SIEMPRE redirige a login.
    El usuario debe iniciar sesión al entrar al sitio.
    Los botones "Abrir IDE" apuntan a /i/<slug>/?editor=true para ir al IDE sin pasar por /.
    """
    return redirect('login')


urlpatterns = [
    path('', root_redirect, name='index'),
    path('api/ports/', views.list_ports, name='list_ports'),
    path('api/compile/', views.compile_code, name='compile'),
    path('api/compile-download/', views.compile_and_download, name='compile_download'),
    path('api/upload/', views.upload_code, name='upload'),
    path('api/hex/<str:token>', views.serve_hex_file, name='serve_hex'),
    path('api/hex/<str:token>.hex', views.serve_hex_file, name='serve_hex_file'),
    path('api/serial/connect/', views.serial_connect, name='serial_connect'),
    path('api/serial/disconnect/', views.serial_disconnect, name='serial_disconnect'),
    path('api/serial/read/', views.serial_read, name='serial_read'),
    path('api/serial/write/', views.serial_write, name='serial_write'),
    path('api/serial/status/', views.serial_status, name='serial_status'),
    path('admin/', deprecated_redirect, name='admin_dashboard_legacy'),
    path('admin/<path:subpath>', deprecated_redirect),
    path('api/ide/autosave/', ide_views.api_ide_autosave, name='api_ide_autosave'),
    path('api/ide/snapshot/', ide_views.api_ide_create_snapshot, name='api_ide_create_snapshot'),
    path('api/ide/project/<str:project_id>/', ide_views.api_ide_load_project, name='api_ide_load_project'),
    path('api/ide/projects/', ide_views.api_ide_list_projects, name='api_ide_list_projects'),
    path('api/ide/projects/create/', ide_views.api_ide_create_project, name='api_ide_create_project'),
    path('api/ide/projects/save-as/', ide_views.api_ide_save_as, name='api_ide_save_as'),
    path('api/ide/projects/<str:project_id>/rename/', ide_views.api_ide_rename_project, name='api_ide_rename_project'),
    path('api/ide/projects/<str:project_id>/delete/', ide_views.api_ide_delete_project, name='api_ide_delete_project'),
    # Proyectos de estudiante (mismo handler que bajo /i/<slug>/; rutas en raíz para fetch desde cualquier origen)
    path('api/projects/save/', student_views.api_save_project, name='global_api_save_project'),
    path('api/projects/load/<int:project_id>/', student_views.api_load_project, name='global_api_load_project'),
    path('api/projects/list/', student_views.api_list_projects, name='global_api_list_projects'),
    path('api/projects/create/', student_views.api_create_project, name='global_api_create_project'),
    path('api/projects/delete/<int:project_id>/', student_views.api_delete_project, name='global_api_delete_project'),
    path('api/agent/register/', agent_views.api_agent_register, name='api_agent_register'),
    path('api/agent/heartbeat/', agent_views.api_agent_heartbeat, name='api_agent_heartbeat'),
    path('api/agent/list/', agent_views.api_agent_list, name='api_agent_list'),
    path('api/agent/<str:agent_id>/', agent_views.api_agent_status, name='api_agent_status'),
    path('api/agent/check/', agent_views.api_agent_check, name='api_agent_check'),
    path('api/errors/', error_views.api_error_create, name='api_error_create'),
    path('api/errors/list/', error_views.api_error_list, name='api_error_list'),
    path('api/notifications/', notification_views.api_notifications_list, name='api_notifications_list'),
    path('api/notifications/mark-all-read/', notification_views.api_notifications_mark_all_read, name='api_notifications_mark_all_read'),
    path('api/notifications/<uuid:notification_id>/mark-read/', notification_views.api_notifications_mark_read, name='api_notifications_mark_read'),
]
