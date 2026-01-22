"""
Vistas del Módulo 4: Integración MAX-IDE con Workspaces multi-tenant
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q

from .models import (
    Institution, Course, Activity, Submission, ActivityWorkspace, IDEProject,
    ProjectSnapshot, Enrollment, TeachingAssignment
)
from .models import UserRoleHelper


# ============================================
# VISTAS DE ESTUDIANTE
# ============================================

@login_required
def student_activity_ide(request, institution_slug, activity_id):
    """Abrir IDE desde una actividad (vista de estudiante)"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    activity = get_object_or_404(Activity, id=activity_id, status='published')
    
    # Verificar que pertenece a la institución
    if activity.institution != institution:
        messages.error(request, 'No tienes permisos para ver esta actividad.')
        return redirect('editor:student_courses_list', institution_slug=institution_slug)
    
    # Verificar que el estudiante está matriculado en el curso
    if not Enrollment.objects.filter(
        course=activity.course,
        student=request.user,
        status='active'
    ).exists() and not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No estás matriculado en este curso.')
        return redirect('editor:student_courses_list', institution_slug=institution_slug)
    
    # Obtener o crear workspace
    workspace, created = ActivityWorkspace.objects.get_or_create(
        activity=activity,
        student=request.user,
        defaults={
            'status': 'in_progress',
            'project': IDEProject.objects.create(
                owner=request.user,
                institution=institution,
                name=f"{activity.title} - {request.user.username}",
                blockly_xml='',
                arduino_code=''
            )
        }
    )
    
    # Si ya existe, usar el proyecto existente
    if not created:
        project = workspace.project
    else:
        project = workspace.project
    
    # Verificar si el workspace está congelado
    is_frozen = workspace.is_frozen()
    is_read_only = is_frozen or (activity.is_closed() or activity.is_deadline_passed())
    
    # Verificar si puede entregar
    can_submit = activity.is_published() and not activity.is_closed() and not activity.is_deadline_passed()
    
    # Obtener última entrega
    last_submission = Submission.objects.filter(
        activity=activity,
        student=request.user
    ).order_by('-attempt').first()
    
    # Si hay entrega y no se permite re-entrega, congelar
    if last_submission and last_submission.status in ['submitted', 'graded']:
        if not activity.allow_resubmit:
            if not workspace.is_frozen():
                workspace.freeze()
                is_frozen = True
                is_read_only = True
        else:
            # Si permite re-entrega, mantener workspace activo
            if workspace.is_frozen():
                workspace.unfreeze()
                is_frozen = False
                is_read_only = False
    
    context = {
        'institution': institution,
        'activity': activity,
        'workspace': workspace,
        'project': project,
        'is_frozen': is_frozen,
        'is_read_only': is_read_only,
        'can_submit': can_submit,
        'last_submission': last_submission,
    }
    return render(request, 'editor/ide/student/activity_ide.html', context)


# ============================================
# VISTAS DE TUTOR
# ============================================

@login_required
def tutor_activity_ide_sandbox(request, institution_slug, activity_id):
    """IDE Sandbox del tutor para probar la actividad"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    activity = get_object_or_404(Activity, id=activity_id)
    
    # Verificar que pertenece a la institución
    if activity.institution != institution:
        messages.error(request, 'No tienes permisos para ver esta actividad.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    # Verificar permisos
    if not TeachingAssignment.objects.filter(
        course=activity.course,
        tutor=request.user,
        status='active'
    ).exists() and not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para abrir el sandbox de esta actividad.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    # Crear proyecto sandbox para el tutor
    sandbox_project, created = IDEProject.objects.get_or_create(
        owner=request.user,
        institution=institution,
        name=f"SANDBOX - {activity.title}",
        defaults={
            'blockly_xml': '',
            'arduino_code': ''
        }
    )
    
    context = {
        'institution': institution,
        'activity': activity,
        'project': sandbox_project,
        'is_sandbox': True,
        'is_read_only': False,
    }
    return render(request, 'editor/ide/tutor/activity_sandbox.html', context)


@login_required
def tutor_submission_ide_readonly(request, institution_slug, submission_id):
    """Ver IDE en modo read-only de una entrega (vista de tutor)"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    submission = get_object_or_404(Submission, id=submission_id)
    activity = submission.activity
    
    # Verificar que pertenece a la institución
    if activity.institution != institution:
        messages.error(request, 'No tienes permisos para ver esta entrega.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    # Verificar permisos
    if not TeachingAssignment.objects.filter(
        course=activity.course,
        tutor=request.user,
        status='active'
    ).exists() and not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para ver esta entrega.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    # Obtener proyecto de la entrega
    artifact_ref = submission.artifact_ref or {}
    project_id = artifact_ref.get('project_id')
    
    if not project_id:
        messages.error(request, 'Esta entrega no tiene un proyecto asociado.')
        return redirect('editor:tutor_activity_submissions', institution_slug=institution_slug, activity_id=activity.id)
    
    # Obtener proyecto (puede ser un IDEProject o un Project legacy)
    try:
        project = IDEProject.objects.get(id=project_id)
    except IDEProject.DoesNotExist:
        # Intentar con Project legacy
        from .models import Project
        try:
            project = Project.objects.get(id=project_id)
            # Convertir a IDEProject si es necesario
            project = IDEProject.objects.create(
                owner=submission.student,
                institution=institution,
                name=project.name,
                blockly_xml=project.xml_content or '',
                arduino_code=project.arduino_code or ''
            )
        except Project.DoesNotExist:
            messages.error(request, 'No se pudo encontrar el proyecto asociado a esta entrega.')
            return redirect('editor:tutor_activity_submissions', institution_slug=institution_slug, activity_id=activity.id)
    
    context = {
        'institution': institution,
        'activity': activity,
        'submission': submission,
        'project': project,
        'is_read_only': True,
    }
    return render(request, 'editor/ide/tutor/submission_readonly.html', context)


# ============================================
# APIs para IDE
# ============================================

@login_required
@require_POST
def api_ide_autosave(request):
    """API para autosave del IDE"""
    try:
        # Soportar tanto POST form data como JSON
        if request.content_type == 'application/json':
            import json
            data = json.loads(request.body)
            project_id = data.get('project_id')
            blockly_xml = data.get('xml_content') or data.get('blockly_xml', '')
            arduino_code = data.get('arduino_code', '')
        else:
            project_id = request.POST.get('project_id')
            blockly_xml = request.POST.get('blockly_xml', '')
            arduino_code = request.POST.get('arduino_code', '')
        
        if not project_id:
            return JsonResponse({'ok': False, 'error': 'project_id requerido'}, status=400)
        
        project = get_object_or_404(IDEProject, id=project_id)
        
        # Verificar permisos
        if project.owner != request.user:
            return JsonResponse({'ok': False, 'error': 'No tienes permisos para editar este proyecto'}, status=403)
        
        # Verificar si está congelado
        if project.is_frozen():
            return JsonResponse({'ok': False, 'error': 'El proyecto está congelado (read-only)'}, status=403)
        
        # Actualizar con transacción para evitar conflictos
        with transaction.atomic():
            project.blockly_xml = blockly_xml
            project.arduino_code = arduino_code
            project.save()
        
        return JsonResponse({
            'ok': True,
            'message': 'Proyecto guardado exitosamente',
            'updated_at': project.updated_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def api_ide_create_snapshot(request):
    """API para crear snapshot del proyecto"""
    try:
        project_id = request.POST.get('project_id')
        label = request.POST.get('label', '')
        
        if not project_id:
            return JsonResponse({'ok': False, 'error': 'project_id requerido'}, status=400)
        
        project = get_object_or_404(IDEProject, id=project_id)
        
        # Verificar permisos
        if project.owner != request.user:
            return JsonResponse({'ok': False, 'error': 'No tienes permisos para crear snapshot'}, status=403)
        
        # Crear snapshot
        snapshot = ProjectSnapshot.objects.create(
            project=project,
            label=label or f"Snapshot {timezone.now().strftime('%Y-%m-%d %H:%M')}",
            blockly_xml=project.blockly_xml,
            arduino_code=project.arduino_code
        )
        
        return JsonResponse({
            'ok': True,
            'message': 'Snapshot creado exitosamente',
            'snapshot_id': str(snapshot.id)
        })
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET", "POST"])
def api_ide_load_project(request, project_id):
    """API para cargar un proyecto del IDE"""
    try:
        project = get_object_or_404(IDEProject, id=project_id)
        
        # Verificar permisos
        if project.owner != request.user and not UserRoleHelper.user_has_role(
            request.user, ['admin', 'institution', 'tutor'], project.institution
        ):
            return JsonResponse({'ok': False, 'error': 'No tienes permisos para ver este proyecto'}, status=403)
        
        return JsonResponse({
            'ok': True,
            'project': {
                'id': str(project.id),
                'name': project.name,
                'blockly_xml': project.blockly_xml,
                'arduino_code': project.arduino_code,
                'updated_at': project.updated_at.isoformat(),
                'is_read_only': project.is_frozen(),
            }
        })
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


# ============================================
# APIs para Mis Proyectos (Borradores)
# ============================================

@login_required
def api_ide_list_projects(request):
    """API para listar proyectos del usuario actual"""
    try:
        # Obtener proyectos del usuario ordenados por última modificación
        projects = IDEProject.objects.filter(
            owner=request.user
        ).exclude(
            # Excluir proyectos vinculados a actividades (workspaces)
            activity_workspaces__isnull=False
        ).order_by('-updated_at')[:20]  # Últimos 20 proyectos
        
        projects_list = [{
            'id': str(p.id),
            'name': p.name,
            'updated_at': p.updated_at.strftime('%d/%m/%Y %H:%M'),
            'is_frozen': p.is_frozen(),
        } for p in projects]
        
        return JsonResponse({
            'ok': True,
            'projects': projects_list,
            'count': len(projects_list)
        })
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def api_ide_create_project(request):
    """API para crear un nuevo proyecto"""
    try:
        import json
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        name = data.get('name', '').strip()
        blockly_xml = data.get('blockly_xml', '')
        arduino_code = data.get('arduino_code', '')
        institution_slug = data.get('institution_slug', '')
        
        if not name:
            name = f"Proyecto {timezone.now().strftime('%d/%m/%Y %H:%M')}"
        
        # Obtener institución (opcional)
        institution = None
        if institution_slug:
            institution = Institution.objects.filter(slug=institution_slug, status='active').first()
        
        # Si no hay institución, intentar obtener la del usuario
        if not institution:
            from .models import Membership
            membership = Membership.objects.filter(user=request.user, is_active=True).first()
            if membership:
                institution = membership.institution
        
        if not institution:
            return JsonResponse({'ok': False, 'error': 'No se pudo determinar la institución'}, status=400)
        
        # Crear proyecto
        project = IDEProject.objects.create(
            owner=request.user,
            institution=institution,
            name=name,
            blockly_xml=blockly_xml,
            arduino_code=arduino_code
        )
        
        return JsonResponse({
            'ok': True,
            'message': 'Proyecto creado exitosamente',
            'project': {
                'id': str(project.id),
                'name': project.name,
                'updated_at': project.updated_at.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def api_ide_rename_project(request, project_id):
    """API para renombrar un proyecto"""
    try:
        import json
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        new_name = data.get('name', '').strip()
        
        if not new_name:
            return JsonResponse({'ok': False, 'error': 'El nombre no puede estar vacío'}, status=400)
        
        project = get_object_or_404(IDEProject, id=project_id)
        
        # Verificar permisos
        if project.owner != request.user:
            return JsonResponse({'ok': False, 'error': 'No tienes permisos para renombrar este proyecto'}, status=403)
        
        project.name = new_name
        project.save()
        
        return JsonResponse({
            'ok': True,
            'message': 'Proyecto renombrado exitosamente',
            'name': project.name
        })
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def api_ide_delete_project(request, project_id):
    """API para eliminar un proyecto"""
    try:
        project = get_object_or_404(IDEProject, id=project_id)
        
        # Verificar permisos
        if project.owner != request.user:
            return JsonResponse({'ok': False, 'error': 'No tienes permisos para eliminar este proyecto'}, status=403)
        
        # Verificar que no esté vinculado a una actividad
        if project.activity_workspaces.exists():
            return JsonResponse({'ok': False, 'error': 'No puedes eliminar un proyecto vinculado a una actividad'}, status=400)
        
        project_name = project.name
        project.delete()
        
        return JsonResponse({
            'ok': True,
            'message': f'Proyecto "{project_name}" eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@require_POST  
def api_ide_save_as(request):
    """API para guardar proyecto actual como nuevo (Guardar como...)"""
    try:
        import json
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        name = data.get('name', '').strip()
        blockly_xml = data.get('blockly_xml', '')
        arduino_code = data.get('arduino_code', '')
        source_project_id = data.get('source_project_id', '')
        institution_slug = data.get('institution_slug', '')
        
        if not name:
            return JsonResponse({'ok': False, 'error': 'El nombre es requerido'}, status=400)
        
        # Obtener institución
        institution = None
        if institution_slug:
            institution = Institution.objects.filter(slug=institution_slug, status='active').first()
        
        # Intentar obtener del proyecto fuente
        if not institution and source_project_id:
            source_project = IDEProject.objects.filter(id=source_project_id).first()
            if source_project:
                institution = source_project.institution
        
        # Si no hay institución, usar la del membership
        if not institution:
            from .models import Membership
            membership = Membership.objects.filter(user=request.user, is_active=True).first()
            if membership:
                institution = membership.institution
        
        if not institution:
            return JsonResponse({'ok': False, 'error': 'No se pudo determinar la institución'}, status=400)
        
        # Crear nuevo proyecto
        project = IDEProject.objects.create(
            owner=request.user,
            institution=institution,
            name=name,
            blockly_xml=blockly_xml,
            arduino_code=arduino_code
        )
        
        return JsonResponse({
            'ok': True,
            'message': f'Proyecto "{name}" guardado exitosamente',
            'project': {
                'id': str(project.id),
                'name': project.name,
                'updated_at': project.updated_at.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)
