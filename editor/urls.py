from django.urls import path
from . import views
from . import management_views
from . import student_views
from . import auth_views

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
]
