from django.urls import path, include
from . import views
from . import management_views
from . import student_views
from . import auth_views
from . import academic_views
from . import activity_views
from . import ide_views
from . import agent_views
from . import error_views

app_name = 'editor'

urlpatterns = [
    # Autenticación
    path('login/', auth_views.student_login, name='login'),
    path('admin-login/', auth_views.admin_login, name='admin_login'),
    
    # Vista principal
    path('', views.index, name='index'),
    
    # API Arduino
    path('api/ports/', views.list_ports, name='list_ports'),
    path('api/compile/', views.compile_code, name='compile'),
    path('api/compile-download/', views.compile_and_download, name='compile_download'),
    path('api/upload/', views.upload_code, name='upload'),
    path('api/hex/<str:token>', views.serve_hex_file, name='serve_hex'),
    path('api/hex/<str:token>.hex', views.serve_hex_file, name='serve_hex_file'),
    
    # API Monitor Serial
    path('api/serial/connect/', views.serial_connect, name='serial_connect'),
    path('api/serial/disconnect/', views.serial_disconnect, name='serial_disconnect'),
    path('api/serial/read/', views.serial_read, name='serial_read'),
    path('api/serial/write/', views.serial_write, name='serial_write'),
    path('api/serial/status/', views.serial_status, name='serial_status'),
    
    # Vistas de Administración
    path('admin/', management_views.admin_dashboard, name='admin_dashboard'),
    path('admin/institutions/', management_views.institutions_list, name='institutions_list'),
    path('admin/institutions/create/', management_views.institution_create, name='institution_create'),
    path('admin/courses/', management_views.courses_list, name='courses_list'),
    path('admin/courses/create/', management_views.course_create, name='course_create'),
    path('admin/students/', management_views.students_list, name='students_list'),
    path('admin/students/create/', management_views.student_create, name='student_create'),
    path('admin/students/<int:student_id>/', management_views.student_detail, name='student_detail'),
    
    # Vistas de Estudiante
    path('student/', student_views.student_dashboard, name='student_dashboard'),
    path('student/projects/', student_views.student_projects, name='student_projects'),
    path('student/projects/<int:project_id>/', student_views.project_detail, name='project_detail'),
    
    # API de Proyectos
    path('api/projects/save/', student_views.api_save_project, name='api_save_project'),
    path('api/projects/load/<int:project_id>/', student_views.api_load_project, name='api_load_project'),
    path('api/projects/list/', student_views.api_list_projects, name='api_list_projects'),
    path('api/projects/create/', student_views.api_create_project, name='api_create_project'),
    path('api/projects/delete/<int:project_id>/', student_views.api_delete_project, name='api_delete_project'),
    
    # ============================================
    # MÓDULO 2: Estructura Académica (con tenant scoping)
    # Estas rutas deben ser incluidas bajo /i/<slug>/ en arduino_ide/urls.py
    # ============================================
    
    # Vistas de Institución
    path('institution/courses/', academic_views.institution_courses_list, name='institution_courses_list'),
    path('institution/courses/new/', academic_views.institution_course_create, name='institution_course_create'),
    path('institution/courses/<int:course_id>/edit/', academic_views.institution_course_edit, name='institution_course_edit'),
    path('institution/courses/<int:course_id>/', academic_views.institution_course_detail, name='institution_course_detail'),
    path('institution/courses/<int:course_id>/assign-tutor/', academic_views.institution_course_assign_tutor, name='institution_course_assign_tutor'),
    path('institution/courses/<int:course_id>/enroll/', academic_views.institution_enroll_student, name='institution_enroll_student'),
    path('institution/enrollments/import-csv/', academic_views.institution_import_csv, name='institution_import_csv'),
    
    # Vistas de Tutor
    path('tutor/courses/', academic_views.tutor_courses_list, name='tutor_courses_list'),
    path('tutor/courses/<int:course_id>/roster/', academic_views.tutor_course_roster, name='tutor_course_roster'),
    
    # Vistas de Estudiante
    path('student/courses/', academic_views.student_courses_list, name='student_courses_list'),
    
    # ============================================
    # MÓDULO 3: Actividades y Entregas (con tenant scoping)
    # ============================================
    
    # Vistas de Tutor
    path('tutor/courses/<int:course_id>/activities/', activity_views.tutor_activities_list, name='tutor_activities_list'),
    path('tutor/activities/new/', activity_views.tutor_activity_create, name='tutor_activity_create'),
    path('tutor/activities/<str:activity_id>/edit/', activity_views.tutor_activity_edit, name='tutor_activity_edit'),
    path('tutor/activities/<str:activity_id>/publish/', activity_views.tutor_activity_publish, name='tutor_activity_publish'),
    path('tutor/activities/<str:activity_id>/submissions/', activity_views.tutor_activity_submissions, name='tutor_activity_submissions'),
    path('tutor/submissions/<str:submission_id>/grade/', activity_views.tutor_submission_grade, name='tutor_submission_grade'),
    
    # Vistas de Estudiante
    path('student/courses/<int:course_id>/activities/', activity_views.student_activities_list, name='student_activities_list'),
    path('student/activities/<str:activity_id>/', activity_views.student_activity_detail, name='student_activity_detail'),
    path('student/activities/<str:activity_id>/submit/', activity_views.student_activity_submit, name='student_activity_submit'),
    path('student/submissions/<str:submission_id>/feedback/', activity_views.student_submission_feedback, name='student_submission_feedback'),
    
    # ============================================
    # MÓDULO 4: IDE y Workspaces (con tenant scoping)
    # ============================================
    
    # Vistas de Estudiante
    path('student/activities/<str:activity_id>/ide/', ide_views.student_activity_ide, name='student_activity_ide'),
    
    # Vistas de Tutor
    path('tutor/activities/<str:activity_id>/ide-sandbox/', ide_views.tutor_activity_ide_sandbox, name='tutor_activity_ide_sandbox'),
    path('tutor/submissions/<str:submission_id>/ide-readonly/', ide_views.tutor_submission_ide_readonly, name='tutor_submission_ide_readonly'),
    
    # APIs de IDE
    path('api/ide/autosave/', ide_views.api_ide_autosave, name='api_ide_autosave'),
    path('api/ide/snapshot/', ide_views.api_ide_create_snapshot, name='api_ide_create_snapshot'),
    path('api/ide/project/<str:project_id>/', ide_views.api_ide_load_project, name='api_ide_load_project'),
    
    # ============================================
    # MÓDULO 5: Agent Local Institucional (con tenant scoping)
    # ============================================
    
    # APIs del Agent (sin autenticación de usuario, solo token)
    path('api/agent/register/', agent_views.api_agent_register, name='api_agent_register'),
    path('api/agent/heartbeat/', agent_views.api_agent_heartbeat, name='api_agent_heartbeat'),
    path('api/agent/list/', agent_views.api_agent_list, name='api_agent_list'),
    path('api/agent/<str:agent_id>/', agent_views.api_agent_status, name='api_agent_status'),
    path('api/agent/check/', agent_views.api_agent_check, name='api_agent_check'),
    
    # Vistas de Institución
    path('institution/agents/', agent_views.institution_agents_list, name='institution_agents_list'),
    path('institution/agents/<str:agent_id>/', agent_views.institution_agent_detail, name='institution_agent_detail'),
    
    # ============================================
    # MÓDULO 6: Observabilidad (ErrorEvent/AuditLog)
    # ============================================
    
    # APIs de Errores
    path('api/errors/', error_views.api_error_create, name='api_error_create'),
    path('api/errors/list/', error_views.api_error_list, name='api_error_list'),
    
    # Vistas de Institución
    path('institution/errors/', error_views.institution_errors_list, name='institution_errors_list'),
    
    # Vistas de Tutor
    path('tutor/errors/', error_views.tutor_errors_list, name='tutor_errors_list'),
]
