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
from . import institution_views
from . import tutor_views
from . import group_views
from . import activity_group_views

app_name = 'editor'

urlpatterns = [
    # Autenticación (comentado - se usa la vista de Django en arduino_ide/urls.py)
    # path('login/', auth_views.student_login, name='login'),
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
    # MÓDULO 2: Institución (solo lectura)
    # CRUD de Institution vive en Django Admin (/admin/)
    # ============================================
    
    # Vista read-only "Mi Institución"
    path('my-institution/', institution_views.my_institution, name='my_institution'),
    path('tutor/my-institution/', institution_views.tutor_my_institution, name='tutor_my_institution'),
    path('student/my-institution/', institution_views.student_my_institution, name='student_my_institution'),
    
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
    
    # ============================================
    # MÓDULO 3: Perfil de Tutor (solo lectura)
    # CRUD de TutorProfile vive en Django Admin (/admin/)
    # ============================================
    
    path('tutor/profile/', tutor_views.tutor_profile, name='tutor_profile'),
    path('api/tutor/status/', tutor_views.check_tutor_status, name='api_tutor_status'),
    
    # Vistas de Tutor - Cursos
    path('tutor/courses/', academic_views.tutor_courses_list, name='tutor_courses_list'),
    path('tutor/courses/new/', academic_views.tutor_course_create, name='tutor_course_create'),
    path('tutor/courses/<int:course_id>/roster/', academic_views.tutor_course_roster, name='tutor_course_roster'),
    path('tutor/courses/<int:course_id>/enroll/', academic_views.tutor_enroll_student, name='tutor_enroll_student'),
    
    # ============================================
    # MÓDULO 4: Grupos y Estudiantes
    # Tutor gestiona; Admin supervisa en Django Admin (/admin/)
    # ============================================
    
    # Grupos (Tutor)
    path('tutor/groups/', group_views.tutor_groups_list, name='tutor_groups_list'),
    path('tutor/groups/new/', group_views.tutor_group_create, name='tutor_group_create'),
    path('tutor/groups/<uuid:group_id>/', group_views.tutor_group_detail, name='tutor_group_detail'),
    path('tutor/groups/<uuid:group_id>/edit/', group_views.tutor_group_edit, name='tutor_group_edit'),
    path('tutor/groups/<uuid:group_id>/delete/', group_views.tutor_group_delete, name='tutor_group_delete'),
    
    # Estudiantes (Tutor)
    path('tutor/students/', group_views.tutor_students_list, name='tutor_students_list'),
    path('tutor/students/new/', group_views.tutor_student_create, name='tutor_student_create_new'),
    path('tutor/students/<int:student_id>/', group_views.tutor_student_detail, name='tutor_student_detail'),
    path('tutor/students/<int:student_id>/edit/', group_views.tutor_student_edit, name='tutor_student_edit'),
    path('api/tutor/assign-group/', group_views.tutor_assign_student_to_group, name='tutor_assign_student_to_group'),
    
    # Mi Contexto (Estudiante)
    path('student/my-info/', group_views.student_my_context, name='student_my_context'),
    
    # Vistas de Estudiante - Cursos
    path('student/courses/', academic_views.student_courses_list, name='student_courses_list'),
    
    # ============================================
    # MÓDULO 5: Actividades y Entregas por Grupo
    # Tutor UI + Estudiante UI; Admin via Django Admin
    # ============================================
    
    # Tutor: Actividades por Grupo
    path('tutor/groups/<uuid:group_id>/activities/', activity_group_views.tutor_group_activities_list, name='tutor_group_activities_list'),
    path('tutor/groups/<uuid:group_id>/activities/new/', activity_group_views.tutor_group_activity_create, name='tutor_group_activity_create'),
    path('tutor/groups/<uuid:group_id>/activities/<uuid:activity_id>/edit/', activity_group_views.tutor_group_activity_edit, name='tutor_group_activity_edit'),
    path('tutor/activities/<uuid:activity_id>/submissions/', activity_group_views.tutor_activity_submissions, name='tutor_activity_submissions_list'),
    path('tutor/submissions/<uuid:submission_id>/', activity_group_views.tutor_submission_detail, name='tutor_submission_detail'),
    path('tutor/submissions/<uuid:submission_id>/grade/', activity_group_views.tutor_submission_grade, name='tutor_submission_grade_form'),
    
    # Estudiante: Actividades de su Grupo
    path('student/activities/', activity_group_views.student_group_activities, name='student_group_activities'),
    path('student/activities/<uuid:activity_id>/', activity_group_views.student_activity_detail, name='student_activity_detail_view'),
    path('student/activities/<uuid:activity_id>/ide/', activity_group_views.student_activity_ide, name='student_activity_ide_view'),
    
    # APIs de Actividades por Grupo
    path('api/activity/<uuid:activity_id>/submit/', activity_group_views.api_submit_activity, name='api_submit_activity'),
    path('api/activity/<uuid:activity_id>/save/', activity_group_views.api_save_activity_progress, name='api_save_activity_progress'),
    
    # ============================================
    # Actividades y Entregas por Curso (legacy)
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
    path('student/activities/<str:activity_id>/status/', activity_views.api_submission_status, name='api_submission_status'),
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
