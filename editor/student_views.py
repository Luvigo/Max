"""
Vistas para estudiantes y tutores - gestión de proyectos Arduino (modelo Project).
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Student, Project, Institution, Membership


def _institution_for_student(student):
    if student.institution_id:
        return student.institution
    if student.group_id:
        return student.group.institution
    if student.course_id:
        return student.course.institution
    return None


def _resolve_student_for_tenant(request, institution_slug):
    """
    institution_slug viene del include /i/<slug>/... en urls.
    Valida que el estudiante pertenezca a esa institución (directa o vía grupo).
    """
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        return institution, None, 'no_profile'
    allowed_ids = []
    if student.institution_id:
        allowed_ids.append(student.institution_id)
    if student.group_id and student.group.institution_id:
        allowed_ids.append(student.group.institution_id)
    if institution.id not in allowed_ids:
        return institution, None, 'wrong_tenant'
    return institution, student, None


def _resolve_project_api_actor(request, institution_slug=None):
    """
    Quién puede usar /api/projects/* en este contexto.
    Devuelve (mode, student|None, tutor_user|None, institution|None).
    mode es 'student' o 'tutor'. Si no hay permiso, (None, None, None, None).
    """
    if institution_slug:
        institution = get_object_or_404(Institution, slug=institution_slug, status='active')
        _, student, _err = _resolve_student_for_tenant(request, institution_slug)
        if student is not None:
            return 'student', student, None, institution
        if request.user.is_superuser or Membership.objects.filter(
            user=request.user,
            institution=institution,
            is_active=True,
            role='tutor',
        ).exists():
            return 'tutor', None, request.user, institution
        return None, None, None, None

    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        return None, None, None, None
    inst = _institution_for_student(student)
    return 'student', student, None, inst


def _get_student_for_project_api(request, institution_slug=None):
    """
    Compat: solo perfil estudiante (APIs globales sin slug o con slug estudiante).
    """
    mode, student, _tutor, _inst = _resolve_project_api_actor(request, institution_slug)
    if mode == 'student':
        return student
    return None


def _forbid_projects_response(institution_slug):
    if institution_slug:
        return JsonResponse({
            'success': False,
            'error': 'No tienes permiso para gestionar proyectos en esta institución',
        }, status=403)
    return JsonResponse({
        'success': False,
        'error': 'No tienes un perfil de estudiante',
    }, status=403)


def _require_tutor_institution(request, institution_slug):
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    if request.user.is_superuser:
        return institution, None
    if Membership.objects.filter(
        user=request.user,
        institution=institution,
        is_active=True,
        role='tutor',
    ).exists():
        return institution, None
    messages.error(request, 'No tienes acceso como tutor a esta institución.')
    return None, redirect('dashboard')


@login_required
def student_dashboard(request, institution_slug):
    """Panel principal del estudiante"""
    institution, student, err = _resolve_student_for_tenant(request, institution_slug)
    if err == 'no_profile':
        messages.error(request, 'No tienes un perfil de estudiante. Contacta al administrador.')
        return redirect('dashboard')
    if err == 'wrong_tenant':
        messages.error(request, 'No tienes acceso a esta institución.')
        return redirect('dashboard')

    projects = student.projects.filter(is_active=True).order_by('-updated_at')[:10]
    projects_count = student.projects.filter(is_active=True).count()

    context = {
        'student': student,
        'projects': projects,
        'projects_count': projects_count,
        'institution': institution,
    }
    return render(request, 'editor/student/dashboard.html', context)


@login_required
def student_projects(request, institution_slug):
    """Lista de proyectos del estudiante"""
    institution, student, err = _resolve_student_for_tenant(request, institution_slug)
    if err == 'no_profile':
        messages.error(request, 'No tienes un perfil de estudiante.')
        return redirect('dashboard')
    if err == 'wrong_tenant':
        messages.error(request, 'No tienes acceso a esta institución.')
        return redirect('dashboard')

    projects = student.projects.filter(is_active=True).order_by('-updated_at')
    return render(request, 'editor/student/projects_list.html', {
        'student': student,
        'projects': projects,
        'institution': institution,
    })


@login_required
def tutor_projects(request, institution_slug):
    """Lista de proyectos personales del tutor (mismo modelo que estudiante)."""
    institution, redir = _require_tutor_institution(request, institution_slug)
    if redir:
        return redir

    projects = Project.objects.filter(
        tutor_owner=request.user,
        institution=institution,
        is_active=True,
    ).order_by('-updated_at')

    return render(request, 'dashboards/tutor_projects_list.html', {
        'institution': institution,
        'user_role': 'tutor',
        'projects': projects,
        'page_title': f'Mis Proyectos - {institution.name}',
    })


@login_required
def project_detail(request, institution_slug, project_id):
    """Detalle de un proyecto - abre MAX-IDE con el proyecto"""
    institution, student, err = _resolve_student_for_tenant(request, institution_slug)
    if err == 'no_profile':
        messages.error(request, 'No tienes un perfil de estudiante.')
        return redirect('dashboard')
    if err == 'wrong_tenant':
        messages.error(request, 'No tienes acceso a esta institución.')
        return redirect('dashboard')

    project = get_object_or_404(Project, id=project_id, student=student, is_active=True)

    return render(request, 'editor/index.html', {
        'institution': institution,
        'project': project,
        'project_xml': project.xml_content,
        'project_code': project.arduino_code
    })


@login_required
def tutor_project_detail(request, institution_slug, project_id):
    """Abre MAX-IDE con un proyecto guardado por el tutor."""
    institution, redir = _require_tutor_institution(request, institution_slug)
    if redir:
        return redir

    project = get_object_or_404(
        Project,
        id=project_id,
        tutor_owner=request.user,
        institution=institution,
        is_active=True,
    )

    return render(request, 'editor/index.html', {
        'institution': institution,
        'project': project,
        'project_xml': project.xml_content,
        'project_code': project.arduino_code,
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_save_project(request, institution_slug=None):
    """API para guardar proyecto desde MAX-IDE"""
    mode, student, tutor_user, institution = _resolve_project_api_actor(request, institution_slug)
    if mode is None:
        return _forbid_projects_response(institution_slug)

    try:
        data = json.loads(request.body)
        project_id = data.get('project_id')
        name = data.get('name', 'Proyecto sin nombre')
        xml_content = data.get('xml_content', '')
        arduino_code = data.get('arduino_code', '')

        if project_id:
            if mode == 'student':
                project = get_object_or_404(
                    Project, id=project_id, student=student, is_active=True
                )
            else:
                project = get_object_or_404(
                    Project,
                    id=project_id,
                    tutor_owner=tutor_user,
                    institution=institution,
                    is_active=True,
                )
            project.name = name
            project.xml_content = xml_content
            project.arduino_code = arduino_code
            project.save()
        else:
            if mode == 'student':
                inst = institution if institution_slug else _institution_for_student(student)
                project = Project.objects.create(
                    student=student,
                    institution=inst,
                    name=name,
                    xml_content=xml_content,
                    arduino_code=arduino_code,
                )
            else:
                project = Project.objects.create(
                    tutor_owner=tutor_user,
                    institution=institution,
                    name=name,
                    xml_content=xml_content,
                    arduino_code=arduino_code,
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
def api_load_project(request, project_id, institution_slug=None):
    """API para cargar proyecto en MAX-IDE"""
    mode, student, tutor_user, institution = _resolve_project_api_actor(request, institution_slug)
    if mode is None:
        return _forbid_projects_response(institution_slug)

    if mode == 'student':
        project = get_object_or_404(Project, id=project_id, student=student, is_active=True)
    else:
        project = get_object_or_404(
            Project,
            id=project_id,
            tutor_owner=tutor_user,
            institution=institution,
            is_active=True,
        )

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
def api_list_projects(request, institution_slug=None):
    """API para listar proyectos del actor actual (estudiante o tutor)."""
    mode, student, tutor_user, institution = _resolve_project_api_actor(request, institution_slug)
    if mode is None:
        return _forbid_projects_response(institution_slug)

    if mode == 'student':
        projects = student.projects.filter(is_active=True).order_by('-updated_at')
    else:
        projects = Project.objects.filter(
            tutor_owner=tutor_user,
            institution=institution,
            is_active=True,
        ).order_by('-updated_at')

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
def api_create_project(request, institution_slug=None):
    """API para crear nuevo proyecto"""
    mode, student, tutor_user, institution = _resolve_project_api_actor(request, institution_slug)
    if mode is None:
        return _forbid_projects_response(institution_slug)

    try:
        data = json.loads(request.body)
        name = data.get('name', 'Nuevo Proyecto')
        description = data.get('description', '')

        if mode == 'student':
            inst = institution if institution_slug else _institution_for_student(student)
            project = Project.objects.create(
                student=student,
                institution=inst,
                name=name,
                description=description
            )
        else:
            project = Project.objects.create(
                tutor_owner=tutor_user,
                institution=institution,
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
def api_delete_project(request, project_id, institution_slug=None):
    """API para eliminar (desactivar) proyecto"""
    mode, student, tutor_user, institution = _resolve_project_api_actor(request, institution_slug)
    if mode is None:
        return _forbid_projects_response(institution_slug)

    if mode == 'student':
        project = get_object_or_404(Project, id=project_id, student=student, is_active=True)
    else:
        project = get_object_or_404(
            Project,
            id=project_id,
            tutor_owner=tutor_user,
            institution=institution,
            is_active=True,
        )
    project.is_active = False
    project.save()

    return JsonResponse({'success': True, 'message': 'Proyecto eliminado exitosamente'})
