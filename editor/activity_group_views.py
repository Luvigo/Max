"""
MÓDULO 5: Actividades y Entregas por Grupo

Tutor UI:
- Crear actividades para grupo
- Ver lista de submissions por actividad
- Ver detalle de submission

Estudiante UI:
- Ver actividades de su grupo
- Abrir IDE por actividad
- Entregar actividad

Admin: Supervisa desde Django Admin (/admin/)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
import json

from .models import (
    Institution, StudentGroup, Student, Activity, Submission, 
    Feedback, IDEProject, ActivityWorkspace
)
from .mixins import tutor_required, student_required


# ============================================
# VISTAS DE TUTOR: ACTIVIDADES POR GRUPO
# ============================================

@login_required
@tutor_required
def tutor_group_activities_list(request, institution_slug, group_id):
    """Lista de actividades de un grupo"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    group = get_object_or_404(
        StudentGroup,
        id=group_id,
        institution=institution,
        tutor=request.user
    )
    
    activities = Activity.objects.filter(
        group=group
    ).annotate(
        submissions_count=Count('submissions', filter=Q(submissions__status__in=['submitted', 'graded'])),
        pending_count=Count('submissions', filter=Q(submissions__status='submitted'))
    ).order_by('-created_at')
    
    # Filtros
    status_filter = request.GET.get('status', '')
    if status_filter:
        activities = activities.filter(status=status_filter)
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'group': group,
        'activities': activities,
        'status_filter': status_filter,
    }
    return render(request, 'editor/activity/tutor/group_activities_list.html', context)


@login_required
@tutor_required
def tutor_group_activity_create(request, institution_slug, group_id):
    """Crear nueva actividad para un grupo"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    group = get_object_or_404(
        StudentGroup,
        id=group_id,
        institution=institution,
        tutor=request.user
    )
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        objective = request.POST.get('objective', '').strip()
        instructions = request.POST.get('instructions', '').strip()
        deadline_str = request.POST.get('deadline', '').strip()
        status = request.POST.get('status', 'draft')
        allow_resubmit = request.POST.get('allow_resubmit') == 'on'
        allow_late_submit = request.POST.get('allow_late_submit') == 'on'
        max_score = request.POST.get('max_score', '100')
        
        # Validaciones
        errors = []
        if not title:
            errors.append('El título es requerido.')
        if not instructions:
            errors.append('Las instrucciones son requeridas.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Parsear deadline
                deadline = None
                if deadline_str:
                    deadline = timezone.datetime.fromisoformat(deadline_str.replace('T', ' '))
                    deadline = timezone.make_aware(deadline) if timezone.is_naive(deadline) else deadline
                
                activity = Activity.objects.create(
                    group=group,
                    created_by=request.user,
                    title=title,
                    objective=objective,
                    instructions=instructions,
                    deadline=deadline,
                    status=status,
                    allow_resubmit=allow_resubmit,
                    allow_late_submit=allow_late_submit,
                    max_score=max_score,
                    published_at=timezone.now() if status == 'published' else None
                )
                
                messages.success(request, f'Actividad "{title}" creada exitosamente.')
                return redirect('editor:tutor_group_activities_list', 
                               institution_slug=institution_slug, group_id=group_id)
                
            except Exception as e:
                messages.error(request, f'Error al crear la actividad: {str(e)}')
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'group': group,
    }
    return render(request, 'editor/activity/tutor/group_activity_form.html', context)


@login_required
@tutor_required
def tutor_group_activity_edit(request, institution_slug, group_id, activity_id):
    """Editar actividad de un grupo"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    group = get_object_or_404(
        StudentGroup,
        id=group_id,
        institution=institution,
        tutor=request.user
    )
    activity = get_object_or_404(Activity, id=activity_id, group=group)
    
    if request.method == 'POST':
        activity.title = request.POST.get('title', activity.title).strip()
        activity.objective = request.POST.get('objective', '').strip()
        activity.instructions = request.POST.get('instructions', activity.instructions).strip()
        
        deadline_str = request.POST.get('deadline', '').strip()
        if deadline_str:
            deadline = timezone.datetime.fromisoformat(deadline_str.replace('T', ' '))
            activity.deadline = timezone.make_aware(deadline) if timezone.is_naive(deadline) else deadline
        else:
            activity.deadline = None
        
        new_status = request.POST.get('status', 'draft')
        if new_status == 'published' and activity.status == 'draft':
            activity.published_at = timezone.now()
        activity.status = new_status
        
        activity.allow_resubmit = request.POST.get('allow_resubmit') == 'on'
        activity.allow_late_submit = request.POST.get('allow_late_submit') == 'on'
        activity.max_score = request.POST.get('max_score', '100')
        
        try:
            activity.save()
            messages.success(request, f'Actividad "{activity.title}" actualizada.')
            return redirect('editor:tutor_group_activities_list',
                           institution_slug=institution_slug, group_id=group_id)
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'group': group,
        'activity': activity,
        'edit_mode': True,
    }
    return render(request, 'editor/activity/tutor/group_activity_form.html', context)


@login_required
@tutor_required
def tutor_activity_submissions(request, institution_slug, activity_id):
    """Lista de entregas de una actividad"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    activity = get_object_or_404(Activity, id=activity_id)
    
    # Verificar permisos
    if activity.group and activity.group.tutor != request.user:
        messages.error(request, 'No tienes permisos para ver esta actividad.')
        return redirect('dashboard')
    
    submissions = Submission.objects.filter(
        activity=activity
    ).select_related('student').order_by('-submitted_at', '-created_at')
    
    # Filtros
    status_filter = request.GET.get('status', '')
    if status_filter:
        submissions = submissions.filter(status=status_filter)
    
    # Estadísticas
    stats = {
        'total': activity.get_target_students_count(),
        'submitted': activity.get_submissions_count(),
        'pending': activity.get_pending_submissions_count(),
        'graded': Submission.objects.filter(activity=activity, status='graded').count(),
    }
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'activity': activity,
        'group': activity.group,
        'submissions': submissions,
        'stats': stats,
        'status_filter': status_filter,
    }
    return render(request, 'editor/activity/tutor/activity_submissions.html', context)


@login_required
@tutor_required
def tutor_submission_detail(request, institution_slug, submission_id):
    """Detalle de una entrega"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Verificar permisos
    if submission.activity.group and submission.activity.group.tutor != request.user:
        messages.error(request, 'No tienes permisos para ver esta entrega.')
        return redirect('dashboard')
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'submission': submission,
        'activity': submission.activity,
        'group': submission.activity.group,
    }
    return render(request, 'editor/activity/tutor/submission_detail.html', context)


@login_required
@tutor_required
def tutor_submission_grade(request, institution_slug, submission_id):
    """Calificar una entrega"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Verificar permisos
    if submission.activity.group and submission.activity.group.tutor != request.user:
        messages.error(request, 'No tienes permisos para calificar esta entrega.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        score = request.POST.get('score', '')
        comments = request.POST.get('comments', '').strip()
        
        try:
            score = float(score) if score else None
            if score is not None and (score < 0 or score > float(submission.activity.max_score)):
                messages.error(request, f'La calificación debe estar entre 0 y {submission.activity.max_score}.')
            else:
                submission.grade(score, request.user, comments)
                messages.success(request, f'Entrega de {submission.student_name} calificada.')
                return redirect('editor:tutor_activity_submissions_list',
                               institution_slug=institution_slug, activity_id=submission.activity.id)
        except ValueError:
            messages.error(request, 'Calificación inválida.')
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'submission': submission,
        'activity': submission.activity,
    }
    return render(request, 'editor/activity/tutor/submission_grade.html', context)


# ============================================
# VISTAS DE ESTUDIANTE: ACTIVIDADES
# ============================================

@login_required
@student_required
def student_group_activities(request, institution_slug):
    """Lista de actividades del grupo del estudiante"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Obtener perfil del estudiante
    try:
        student = Student.objects.get(user=request.user, institution=institution)
    except Student.DoesNotExist:
        messages.error(request, 'No tienes un perfil de estudiante.')
        return redirect('dashboard')
    
    if not student.group:
        messages.warning(request, 'No estás asignado a ningún grupo.')
        activities = Activity.objects.none()
    else:
        # Obtener actividades publicadas del grupo
        activities = Activity.objects.filter(
            group=student.group,
            status='published'
        ).order_by('-deadline', '-created_at')
    
    # Agregar información de entrega para cada actividad
    activities_with_submissions = []
    for activity in activities:
        submission = Submission.objects.filter(
            activity=activity,
            student=request.user
        ).order_by('-attempt').first()
        
        can_submit, reason = activity.can_submit(request.user)
        
        activities_with_submissions.append({
            'activity': activity,
            'submission': submission,
            'can_submit': can_submit,
            'submit_reason': reason,
        })
    
    context = {
        'institution': institution,
        'user_role': 'student',
        'student': student,
        'group': student.group,
        'activities_with_submissions': activities_with_submissions,
    }
    return render(request, 'editor/activity/student/group_activities.html', context)


@login_required
@student_required
def student_activity_detail(request, institution_slug, activity_id):
    """Detalle de una actividad para el estudiante"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    activity = get_object_or_404(Activity, id=activity_id, status='published')
    
    # Verificar que el estudiante pertenece al grupo
    try:
        student = Student.objects.get(user=request.user, institution=institution)
    except Student.DoesNotExist:
        messages.error(request, 'No tienes un perfil de estudiante.')
        return redirect('dashboard')
    
    if activity.group and student.group != activity.group:
        messages.error(request, 'No tienes acceso a esta actividad.')
        return redirect('editor:student_group_activities', institution_slug=institution_slug)
    
    # Obtener submission existente
    submission = Submission.objects.filter(
        activity=activity,
        student=request.user
    ).order_by('-attempt').first()
    
    can_submit, reason = activity.can_submit(request.user)
    
    context = {
        'institution': institution,
        'user_role': 'student',
        'student': student,
        'activity': activity,
        'submission': submission,
        'can_submit': can_submit,
        'submit_reason': reason,
    }
    return render(request, 'editor/activity/student/activity_detail.html', context)


@login_required
@student_required
def student_activity_ide(request, institution_slug, activity_id):
    """IDE para trabajar en una actividad"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    activity = get_object_or_404(Activity, id=activity_id, status='published')
    
    # Verificar que el estudiante pertenece al grupo
    try:
        student = Student.objects.get(user=request.user, institution=institution)
    except Student.DoesNotExist:
        messages.error(request, 'No tienes un perfil de estudiante.')
        return redirect('dashboard')
    
    if activity.group and student.group != activity.group:
        messages.error(request, 'No tienes acceso a esta actividad.')
        return redirect('editor:student_group_activities', institution_slug=institution_slug)
    
    # Obtener o crear submission
    submission = Submission.objects.filter(
        activity=activity,
        student=request.user
    ).order_by('-attempt').first()
    
    if not submission:
        # Crear submission pendiente
        submission = Submission.objects.create(
            activity=activity,
            student=request.user,
            status='in_progress',
            attempt=1
        )
    
    # Verificar si es read-only
    can_submit, reason = activity.can_submit(request.user)
    is_read_only = submission.is_read_only or not can_submit
    
    # Cargar contenido previo si existe
    project_xml = submission.xml_content or ''
    
    context = {
        'institution': institution,
        'user_role': 'student',
        'student': student,
        'activity': activity,
        'submission': submission,
        'can_submit': can_submit,
        'submit_reason': reason,
        'is_read_only': is_read_only,
        'project_xml': project_xml,
    }
    return render(request, 'editor/activity/student/activity_ide.html', context)


# ============================================
# API: SUBMIT ACTIVITY
# ============================================

@login_required
@require_POST
def api_submit_activity(request, institution_slug, activity_id):
    """API para entregar una actividad desde el IDE"""
    try:
        institution = get_object_or_404(Institution, slug=institution_slug, status='active')
        activity = get_object_or_404(Activity, id=activity_id)
        
        # Verificar permisos
        can_submit, reason = activity.can_submit(request.user)
        if not can_submit:
            return JsonResponse({
                'ok': False,
                'error': reason
            }, status=400)
        
        # Obtener datos
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        xml_content = data.get('xml_content', '')
        arduino_code = data.get('arduino_code', '')
        notes = data.get('notes', '')
        
        # Obtener o crear submission
        submission = Submission.objects.filter(
            activity=activity,
            student=request.user
        ).order_by('-attempt').first()
        
        if not submission:
            submission = Submission.objects.create(
                activity=activity,
                student=request.user,
                attempt=1
            )
        elif submission.status in ['submitted', 'graded']:
            if activity.allow_resubmit:
                # Crear nuevo intento
                submission = Submission.objects.create(
                    activity=activity,
                    student=request.user,
                    attempt=submission.attempt + 1
                )
            else:
                return JsonResponse({
                    'ok': False,
                    'error': 'Ya entregaste y no se permite re-entrega.'
                }, status=400)
        
        # Marcar como entregada
        submission.submit(xml_content, arduino_code, notes)
        
        return JsonResponse({
            'ok': True,
            'message': 'Actividad entregada exitosamente.',
            'submission_id': str(submission.id),
            'is_late': submission.is_late,
        })
        
    except Exception as e:
        return JsonResponse({
            'ok': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def api_save_activity_progress(request, institution_slug, activity_id):
    """API para guardar progreso de una actividad (autosave)"""
    try:
        institution = get_object_or_404(Institution, slug=institution_slug, status='active')
        activity = get_object_or_404(Activity, id=activity_id)
        
        # Obtener datos
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        xml_content = data.get('xml_content', '')
        arduino_code = data.get('arduino_code', '')
        
        # Obtener submission en progreso
        submission = Submission.objects.filter(
            activity=activity,
            student=request.user,
            status__in=['pending', 'in_progress']
        ).order_by('-attempt').first()
        
        if not submission:
            submission = Submission.objects.create(
                activity=activity,
                student=request.user,
                status='in_progress',
                attempt=1
            )
        
        # Guardar progreso
        submission.xml_content = xml_content
        submission.arduino_code = arduino_code
        submission.status = 'in_progress'
        submission.save()
        
        return JsonResponse({
            'ok': True,
            'message': 'Progreso guardado.',
            'saved_at': submission.updated_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'ok': False,
            'error': str(e)
        }, status=500)
