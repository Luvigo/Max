"""
Vistas de administración para gestionar instituciones, cursos y estudiantes
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q

from .models import Institution, Course, Student, Project, User


def is_admin(user):
    """Verifica si el usuario es administrador"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Panel principal de administración"""
    institutions_count = Institution.objects.filter(is_active=True).count()
    courses_count = Course.objects.filter(is_active=True).count()
    students_count = Student.objects.filter(is_active=True).count()
    projects_count = Project.objects.filter(is_active=True).count()
    
    recent_students = Student.objects.filter(is_active=True).select_related('user', 'course').order_by('-created_at')[:10]
    recent_projects = Project.objects.filter(is_active=True).select_related('student__user', 'student__course').order_by('-created_at')[:10]
    
    context = {
        'institutions_count': institutions_count,
        'courses_count': courses_count,
        'students_count': students_count,
        'projects_count': projects_count,
        'recent_students': recent_students,
        'recent_projects': recent_projects,
    }
    return render(request, 'editor/admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def institutions_list(request):
    """Lista de instituciones"""
    institutions = Institution.objects.all().annotate(
        courses_count=Count('courses', filter=Q(courses__is_active=True)),
        students_count=Count('courses__students', filter=Q(courses__students__is_active=True))
    ).order_by('name')
    return render(request, 'editor/admin/institutions_list.html', {'institutions': institutions})


@login_required
@user_passes_test(is_admin)
def institution_create(request):
    """Crear nueva institución"""
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        description = request.POST.get('description', '')
        
        if Institution.objects.filter(code=code).exists():
            messages.error(request, 'Ya existe una institución con ese código')
        else:
            Institution.objects.create(
                name=name,
                code=code,
                description=description
            )
            messages.success(request, 'Institución creada exitosamente')
            return redirect('editor:institutions_list')
    
    return render(request, 'editor/admin/institution_form.html', {'action': 'Crear'})


@login_required
@user_passes_test(is_admin)
def courses_list(request):
    """Lista de cursos"""
    institution_id = request.GET.get('institution')
    courses = Course.objects.select_related('institution').annotate(
        students_count=Count('students', filter=Q(students__is_active=True))
    ).order_by('institution', 'academic_year', 'name')
    
    if institution_id:
        courses = courses.filter(institution_id=institution_id)
    
    institutions = Institution.objects.filter(is_active=True)
    return render(request, 'editor/admin/courses_list.html', {
        'courses': courses,
        'institutions': institutions,
        'selected_institution': institution_id
    })


@login_required
@user_passes_test(is_admin)
def course_create(request):
    """Crear nuevo curso"""
    if request.method == 'POST':
        institution_id = request.POST.get('institution')
        name = request.POST.get('name')
        code = request.POST.get('code')
        description = request.POST.get('description', '')
        academic_year = request.POST.get('academic_year', '2024-2025')
        
        institution = get_object_or_404(Institution, id=institution_id)
        
        if Course.objects.filter(institution=institution, code=code, academic_year=academic_year).exists():
            messages.error(request, 'Ya existe un curso con ese código en ese año académico')
        else:
            Course.objects.create(
                institution=institution,
                name=name,
                code=code,
                description=description,
                academic_year=academic_year
            )
            messages.success(request, 'Curso creado exitosamente')
            return redirect('editor:courses_list')
    
    institutions = Institution.objects.filter(is_active=True)
    return render(request, 'editor/admin/course_form.html', {
        'action': 'Crear',
        'institutions': institutions
    })


@login_required
@user_passes_test(is_admin)
def students_list(request):
    """Lista de estudiantes"""
    course_id = request.GET.get('course')
    students = Student.objects.select_related('user', 'course__institution').annotate(
        projects_count=Count('projects', filter=Q(projects__is_active=True))
    ).order_by('student_id')
    
    if course_id:
        students = students.filter(course_id=course_id)
    
    courses = Course.objects.filter(is_active=True).select_related('institution')
    return render(request, 'editor/admin/students_list.html', {
        'students': students,
        'courses': courses,
        'selected_course': course_id
    })


@login_required
@user_passes_test(is_admin)
def student_create(request):
    """Crear nuevo estudiante"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        password = request.POST.get('password')
        student_id = request.POST.get('student_id')
        course_id = request.POST.get('course')
        phone = request.POST.get('phone', '')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe')
        elif Student.objects.filter(student_id=student_id).exists():
            messages.error(request, 'El ID de estudiante ya existe')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            course = get_object_or_404(Course, id=course_id) if course_id else None
            Student.objects.create(
                user=user,
                student_id=student_id,
                course=course,
                phone=phone
            )
            messages.success(request, 'Estudiante creado exitosamente')
            return redirect('editor:students_list')
    
    courses = Course.objects.filter(is_active=True).select_related('institution')
    return render(request, 'editor/admin/student_form.html', {
        'action': 'Crear',
        'courses': courses
    })


@login_required
@user_passes_test(is_admin)
def student_detail(request, student_id):
    """Detalle de estudiante con sus proyectos"""
    student = get_object_or_404(Student, id=student_id)
    projects = student.projects.filter(is_active=True).order_by('-updated_at')
    return render(request, 'editor/admin/student_detail.html', {
        'student': student,
        'projects': projects
    })

