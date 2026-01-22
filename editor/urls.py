"""
LIMPIEZA ARQUITECTÓNICA - URLs de Editor

ROLES VÁLIDOS ÚNICOS:
- Admin: SOLO usa Django Admin (/admin/) - NO tiene rutas aquí
- Tutor: Todas las rutas /tutor/*
- Estudiante: Todas las rutas /student/*

❌ ELIMINADOS:
- Rutas de admin (fuera de /admin/)
- Rutas de institution (como rol)
"""
from django.urls import path
from django.shortcuts import redirect
from . import views
from . import student_views
from . import auth_views
from . import academic_views
from . import activity_views
from . import ide_views
from . import agent_views
from . import error_views
from . import institution_views
from . import tutor_views
from . import group_views
from . import activity_group_views

app_name = 'editor'


# Helper para rutas deprecadas
def deprecated_redirect(request, *args, **kwargs):
    """Redirige rutas deprecadas"""
    return redirect('dashboard')


urlpatterns = [
    # ============================================
    # Vista principal - IDE
    # ============================================
    path('', views.index, name='index'),
    
    # ============================================
    # API Arduino (no depende de roles)
    # ============================================
    path('api/ports/', views.list_ports, name='list_ports'),
    path('api/compile/', views.compile_code, name='compile'),
    path('api/compile-download/', views.compile_and_download, name='compile_download'),
    path('api/upload/', views.upload_code, name='upload'),
    path('api/hex/<str:token>', views.serve_hex_file, name='serve_hex'),
    path('api/hex/<str:token>.hex', views.serve_hex_file, name='serve_hex_file'),
    
    # ============================================
    # API Monitor Serial (no depende de roles)
    # ============================================
    path('api/serial/connect/', views.serial_connect, name='serial_connect'),
    path('api/serial/disconnect/', views.serial_disconnect, name='serial_disconnect'),
    path('api/serial/read/', views.serial_read, name='serial_read'),
    path('api/serial/write/', views.serial_write, name='serial_write'),
    path('api/serial/status/', views.serial_status, name='serial_status'),
    
    # ============================================
    # ❌ RUTAS DE ADMIN ELIMINADAS
    # El admin usa SOLO Django Admin (/admin/)
    # ============================================
    path('admin/', deprecated_redirect, name='admin_dashboard_legacy'),
    path('admin/<path:subpath>', deprecated_redirect),
    
    # ============================================
    # Información de Institución (Solo Lectura)
    # Tutor y Estudiante pueden ver su institución
    # ============================================
    path('my-institution/', institution_views.my_institution, name='my_institution'),
    path('tutor/my-institution/', institution_views.tutor_my_institution, name='tutor_my_institution'),
    path('student/my-institution/', institution_views.student_my_institution, name='student_my_institution'),
    
    # ============================================
    # ❌ RUTAS DE INSTITUCIÓN (como rol) ELIMINADAS
    # La institución es SOLO información, no tiene cuenta
    # Estas rutas redirigen a dashboard
    # ============================================
    path('institution/courses/', deprecated_redirect, name='institution_courses_list'),
    path('institution/courses/new/', deprecated_redirect, name='institution_course_create'),
    path('institution/courses/<int:course_id>/edit/', deprecated_redirect, name='institution_course_edit'),
    path('institution/courses/<int:course_id>/', deprecated_redirect, name='institution_course_detail'),
    path('institution/courses/<int:course_id>/assign-tutor/', deprecated_redirect, name='institution_course_assign_tutor'),
    path('institution/courses/<int:course_id>/enroll/', deprecated_redirect, name='institution_enroll_student'),
    path('institution/enrollments/import-csv/', deprecated_redirect, name='institution_import_csv'),
    path('institution/agents/', deprecated_redirect, name='institution_agents_list'),
    path('institution/agents/<str:agent_id>/', deprecated_redirect, name='institution_agent_detail'),
    path('institution/errors/', deprecated_redirect, name='institution_errors_list'),
    
    # ============================================
    # ✅ TUTOR - Perfil (Solo Lectura)
    # CRUD de TutorProfile vive en Django Admin (/admin/)
    # ============================================
    path('tutor/profile/', tutor_views.tutor_profile, name='tutor_profile'),
    path('api/tutor/status/', tutor_views.check_tutor_status, name='api_tutor_status'),
    
    # ============================================
    # ✅ TUTOR - Cursos
    # ============================================
    path('tutor/courses/', academic_views.tutor_courses_list, name='tutor_courses_list'),
    path('tutor/courses/new/', academic_views.tutor_course_create, name='tutor_course_create'),
    path('tutor/courses/<int:course_id>/roster/', academic_views.tutor_course_roster, name='tutor_course_roster'),
    path('tutor/courses/<int:course_id>/enroll/', academic_views.tutor_enroll_student, name='tutor_enroll_student'),
    
    # ============================================
    # ✅ TUTOR - Grupos
    # ============================================
    path('tutor/groups/', group_views.tutor_groups_list, name='tutor_groups_list'),
    path('tutor/groups/new/', group_views.tutor_group_create, name='tutor_group_create'),
    path('tutor/groups/<uuid:group_id>/', group_views.tutor_group_detail, name='tutor_group_detail'),
    path('tutor/groups/<uuid:group_id>/edit/', group_views.tutor_group_edit, name='tutor_group_edit'),
    path('tutor/groups/<uuid:group_id>/delete/', group_views.tutor_group_delete, name='tutor_group_delete'),
    
    # ============================================
    # ✅ TUTOR - Estudiantes
    # ============================================
    path('tutor/students/', group_views.tutor_students_list, name='tutor_students_list'),
    path('tutor/students/new/', group_views.tutor_student_create, name='tutor_student_create_new'),
    path('tutor/students/<int:student_id>/', group_views.tutor_student_detail, name='tutor_student_detail'),
    path('tutor/students/<int:student_id>/edit/', group_views.tutor_student_edit, name='tutor_student_edit'),
    path('api/tutor/assign-group/', group_views.tutor_assign_student_to_group, name='tutor_assign_student_to_group'),
    
    # ============================================
    # ✅ TUTOR - Actividades por Grupo
    # ============================================
    path('tutor/groups/<uuid:group_id>/activities/', activity_group_views.tutor_group_activities_list, name='tutor_group_activities_list'),
    path('tutor/groups/<uuid:group_id>/activities/new/', activity_group_views.tutor_group_activity_create, name='tutor_group_activity_create'),
    path('tutor/groups/<uuid:group_id>/activities/<uuid:activity_id>/edit/', activity_group_views.tutor_group_activity_edit, name='tutor_group_activity_edit'),
    path('tutor/activities/<uuid:activity_id>/submissions/', activity_group_views.tutor_activity_submissions, name='tutor_activity_submissions_list'),
    path('tutor/submissions/<uuid:submission_id>/', activity_group_views.tutor_submission_detail, name='tutor_submission_detail'),
    path('tutor/submissions/<uuid:submission_id>/grade/', activity_group_views.tutor_submission_grade, name='tutor_submission_grade_form'),
    
    # ============================================
    # ✅ TUTOR - Actividades por Curso (legacy)
    # ============================================
    path('tutor/courses/<int:course_id>/activities/', activity_views.tutor_activities_list, name='tutor_activities_list'),
    path('tutor/activities/new/', activity_views.tutor_activity_create, name='tutor_activity_create'),
    path('tutor/activities/<str:activity_id>/edit/', activity_views.tutor_activity_edit, name='tutor_activity_edit'),
    path('tutor/activities/<str:activity_id>/publish/', activity_views.tutor_activity_publish, name='tutor_activity_publish'),
    path('tutor/activities/<str:activity_id>/submissions/', activity_views.tutor_activity_submissions, name='tutor_activity_submissions'),
    path('tutor/submissions/<str:submission_id>/grade/', activity_views.tutor_submission_grade, name='tutor_submission_grade'),
    
    # ============================================
    # ✅ TUTOR - IDE
    # ============================================
    path('tutor/activities/<str:activity_id>/ide-sandbox/', ide_views.tutor_activity_ide_sandbox, name='tutor_activity_ide_sandbox'),
    path('tutor/submissions/<str:submission_id>/ide-readonly/', ide_views.tutor_submission_ide_readonly, name='tutor_submission_ide_readonly'),
    
    # ============================================
    # ✅ TUTOR - Errores
    # ============================================
    path('tutor/errors/', error_views.tutor_errors_list, name='tutor_errors_list'),
    
    # ============================================
    # ✅ ESTUDIANTE - Dashboard básico
    # ============================================
    path('student/', student_views.student_dashboard, name='student_dashboard'),
    path('student/projects/', student_views.student_projects, name='student_projects'),
    path('student/projects/<int:project_id>/', student_views.project_detail, name='project_detail'),
    
    # ============================================
    # ✅ ESTUDIANTE - Mi Contexto
    # ============================================
    path('student/my-info/', group_views.student_my_context, name='student_my_context'),
    
    # ============================================
    # ✅ ESTUDIANTE - Cursos
    # ============================================
    path('student/courses/', academic_views.student_courses_list, name='student_courses_list'),
    
    # ============================================
    # ✅ ESTUDIANTE - Actividades de su Grupo
    # ============================================
    path('student/activities/', activity_group_views.student_group_activities, name='student_group_activities'),
    path('student/activities/<uuid:activity_id>/', activity_group_views.student_activity_detail, name='student_activity_detail_view'),
    path('student/activities/<uuid:activity_id>/ide/', activity_group_views.student_activity_ide, name='student_activity_ide_view'),
    
    # ============================================
    # ✅ ESTUDIANTE - Actividades por Curso (legacy)
    # ============================================
    path('student/courses/<int:course_id>/activities/', activity_views.student_activities_list, name='student_activities_list'),
    path('student/activities/<str:activity_id>/', activity_views.student_activity_detail, name='student_activity_detail'),
    path('student/activities/<str:activity_id>/submit/', activity_views.student_activity_submit, name='student_activity_submit'),
    path('student/activities/<str:activity_id>/status/', activity_views.api_submission_status, name='api_submission_status'),
    path('student/submissions/<str:submission_id>/feedback/', activity_views.student_submission_feedback, name='student_submission_feedback'),
    
    # ============================================
    # ✅ ESTUDIANTE - IDE
    # ============================================
    path('student/activities/<str:activity_id>/ide/', ide_views.student_activity_ide, name='student_activity_ide'),
    
    # ============================================
    # APIs de Proyectos (Estudiante)
    # ============================================
    path('api/projects/save/', student_views.api_save_project, name='api_save_project'),
    path('api/projects/load/<int:project_id>/', student_views.api_load_project, name='api_load_project'),
    path('api/projects/list/', student_views.api_list_projects, name='api_list_projects'),
    path('api/projects/create/', student_views.api_create_project, name='api_create_project'),
    path('api/projects/delete/<int:project_id>/', student_views.api_delete_project, name='api_delete_project'),
    
    # ============================================
    # APIs de Actividades
    # ============================================
    path('api/activity/<uuid:activity_id>/submit/', activity_group_views.api_submit_activity, name='api_submit_activity'),
    path('api/activity/<uuid:activity_id>/save/', activity_group_views.api_save_activity_progress, name='api_save_activity_progress'),
    
    # ============================================
    # APIs de IDE
    # ============================================
    path('api/ide/autosave/', ide_views.api_ide_autosave, name='api_ide_autosave'),
    path('api/ide/snapshot/', ide_views.api_ide_create_snapshot, name='api_ide_create_snapshot'),
    path('api/ide/project/<str:project_id>/', ide_views.api_ide_load_project, name='api_ide_load_project'),
    
    # APIs de Mis Proyectos (Borradores)
    path('api/ide/projects/', ide_views.api_ide_list_projects, name='api_ide_list_projects'),
    path('api/ide/projects/create/', ide_views.api_ide_create_project, name='api_ide_create_project'),
    path('api/ide/projects/save-as/', ide_views.api_ide_save_as, name='api_ide_save_as'),
    path('api/ide/projects/<str:project_id>/rename/', ide_views.api_ide_rename_project, name='api_ide_rename_project'),
    path('api/ide/projects/<str:project_id>/delete/', ide_views.api_ide_delete_project, name='api_ide_delete_project'),
    
    # ============================================
    # APIs de Agent (sin autenticación de usuario)
    # ============================================
    path('api/agent/register/', agent_views.api_agent_register, name='api_agent_register'),
    path('api/agent/heartbeat/', agent_views.api_agent_heartbeat, name='api_agent_heartbeat'),
    path('api/agent/list/', agent_views.api_agent_list, name='api_agent_list'),
    path('api/agent/<str:agent_id>/', agent_views.api_agent_status, name='api_agent_status'),
    path('api/agent/check/', agent_views.api_agent_check, name='api_agent_check'),
    
    # ============================================
    # APIs de Errores
    # ============================================
    path('api/errors/', error_views.api_error_create, name='api_error_create'),
    path('api/errors/list/', error_views.api_error_list, name='api_error_list'),
]
