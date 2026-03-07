"""
URLs globales de Editor - Rutas que NO requieren institution_slug.

Incluidas en la raíz (path '') para IDE, APIs, etc.
Evita conflicto de namespace con editor.urls (tenant) que tiene tutor/student.
"""
from django.urls import path
from django.shortcuts import redirect
from . import views
from . import ide_views
from . import agent_views
from . import error_views
from . import notification_views
from .models import Membership

app_name = 'editor'


def deprecated_redirect(request, *args, **kwargs):
    return redirect('dashboard')


def root_redirect(request):
    """
    La raíz redirige según el contexto:
    - Si ?editor=true y usuario autenticado -> IDE directamente (evita pantalla "Ya estás conectado")
    - Si no autenticado -> login
    """
    want_ide = request.GET.get('editor') == 'true'

    if want_ide and request.user.is_authenticated:
        # Usuario ya logueado quiere el IDE: ir directo, sin pasar por login
        if request.user.is_superuser or request.user.is_staff:
            return redirect('dashboard')  # Admin no tiene IDE en /i/<slug>/
        membership = Membership.objects.filter(
            user=request.user,
            is_active=True,
            role__in=['tutor', 'student']
        ).select_related('institution').first()
        if membership:
            return redirect(f'/i/{membership.institution.slug}/?editor=true')
        return redirect('login')

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
