"""
Vistas para estudiantes - gestión de proyectos
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Student, Project


@login_required
def student_dashboard(request):
    """Panel principal del estudiante"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, 'No tienes un perfil de estudiante. Contacta al administrador.')
        return redirect('editor:index')
    
    projects = student.projects.filter(is_active=True).order_by('-updated_at')[:10]
    projects_count = student.projects.filter(is_active=True).count()
    
    context = {
        'student': student,
        'projects': projects,
        'projects_count': projects_count,
    }
    return render(request, 'editor/student/dashboard.html', context)


@login_required
def student_projects(request):
    """Lista de proyectos del estudiante"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, 'No tienes un perfil de estudiante.')
        return redirect('editor:index')
    
    projects = student.projects.filter(is_active=True).order_by('-updated_at')
    return render(request, 'editor/student/projects_list.html', {
        'student': student,
        'projects': projects
    })


@login_required
def project_detail(request, project_id):
    """Detalle de un proyecto - abre MAX-IDE con el proyecto"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, 'No tienes un perfil de estudiante.')
        return redirect('editor:index')
    
    project = get_object_or_404(Project, id=project_id, student=student, is_active=True)
    
    # Renderizar el editor con el proyecto cargado
    return render(request, 'editor/index.html', {
        'project': project,
        'project_xml': project.xml_content,
        'project_code': project.arduino_code
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_save_project(request):
    """API para guardar proyecto desde MAX-IDE"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No tienes un perfil de estudiante'}, status=403)
    
    try:
        data = json.loads(request.body)
        project_id = data.get('project_id')
        name = data.get('name', 'Proyecto sin nombre')
        xml_content = data.get('xml_content', '')
        arduino_code = data.get('arduino_code', '')
        
        if project_id:
            # Actualizar proyecto existente
            project = get_object_or_404(Project, id=project_id, student=student)
            project.name = name
            project.xml_content = xml_content
            project.arduino_code = arduino_code
            project.save()
        else:
            # Crear nuevo proyecto
            project = Project.objects.create(
                student=student,
                name=name,
                xml_content=xml_content,
                arduino_code=arduino_code
            )
        
        return JsonResponse({
            'success': True,
            'project_id': project.id,
            'message': 'Proyecto guardado exitosamente'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_load_project(request, project_id):
    """API para cargar proyecto en MAX-IDE"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No tienes un perfil de estudiante'}, status=403)
    
    project = get_object_or_404(Project, id=project_id, student=student, is_active=True)
    
    return JsonResponse({
        'success': True,
        'project': {
            'id': project.id,
            'name': project.name,
            'xml_content': project.xml_content,
            'arduino_code': project.arduino_code,
            'updated_at': project.updated_at.isoformat()
        }
    })


@login_required
@require_http_methods(["GET"])
def api_list_projects(request):
    """API para listar proyectos del estudiante"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No tienes un perfil de estudiante'}, status=403)
    
    projects = student.projects.filter(is_active=True).order_by('-updated_at')
    
    return JsonResponse({
        'success': True,
        'projects': [
            {
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'updated_at': p.updated_at.isoformat()
            }
            for p in projects
        ]
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_create_project(request):
    """API para crear nuevo proyecto"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No tienes un perfil de estudiante'}, status=403)
    
    try:
        data = json.loads(request.body)
        name = data.get('name', 'Nuevo Proyecto')
        description = data.get('description', '')
        
        project = Project.objects.create(
            student=student,
            name=name,
            description=description
        )
        
        return JsonResponse({
            'success': True,
            'project_id': project.id,
            'message': 'Proyecto creado exitosamente'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_delete_project(request, project_id):
    """API para eliminar (desactivar) proyecto"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No tienes un perfil de estudiante'}, status=403)
    
    project = get_object_or_404(Project, id=project_id, student=student)
    project.is_active = False
    project.save()
    
    return JsonResponse({'success': True, 'message': 'Proyecto eliminado exitosamente'})

