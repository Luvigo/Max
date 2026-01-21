"""
Vistas del Módulo 3: Actividades y Entregas multi-tenant
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Count, Q

from .models import Institution, Course, Activity, Submission, Rubric, Feedback, Enrollment, TeachingAssignment
from .forms import ActivityForm, SubmissionForm, FeedbackForm, RubricForm
from .models import UserRoleHelper


# ============================================
# VISTAS DE TUTOR
# ============================================

@login_required
def tutor_activities_list(request, institution_slug, course_id):
    """Lista de actividades de un curso (vista de tutor)"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    course = get_object_or_404(Course, id=course_id, institution=institution)
    
    # Verificar que el tutor está asignado al curso
    if not TeachingAssignment.objects.filter(
        course=course,
        tutor=request.user,
        status='active'
    ).exists() and not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para ver este curso.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    activities = Activity.objects.filter(
        course=course
    ).annotate(
        submissions_count=Count('submissions', filter=Q(submissions__status__in=['submitted', 'graded'])),
        pending_count=Count('submissions', filter=Q(submissions__status='submitted'))
    ).order_by('-deadline', '-created_at')
    
    context = {
        'institution': institution,
        'course': course,
        'activities': activities,
    }
    return render(request, 'editor/activity/tutor/activities_list.html', context)


@login_required
def tutor_activity_create(request, institution_slug):
    """Crear nueva actividad"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution', 'tutor'], institution):
        messages.error(request, 'No tienes permisos para crear actividades.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    # Obtener curso si viene en query string
    course_id = request.GET.get('course')
    course = None
    if course_id:
        course = get_object_or_404(Course, id=course_id, institution=institution)
        # Verificar que el tutor está asignado al curso
        if not TeachingAssignment.objects.filter(
            course=course,
            tutor=request.user,
            status='active'
        ).exists() and not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
            messages.error(request, 'No tienes permisos para crear actividades en este curso.')
            return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    if request.method == 'POST':
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            
            if not course:
                course_id = request.POST.get('course')
                if not course_id:
                    messages.error(request, 'Debes seleccionar un curso.')
                    return redirect('editor:tutor_activity_create', institution_slug=institution_slug)
                course = get_object_or_404(Course, id=course_id, institution=institution)
            
            activity.course = course
            
            # Si se publica, guardar fecha de publicación
            if activity.status == 'published':
                activity.published_at = timezone.now()
            
            activity.save()
            messages.success(request, f'Actividad "{activity.title}" creada exitosamente.')
            return redirect('editor:tutor_activities_list', institution_slug=institution_slug, course_id=course.id)
    else:
        form = ActivityForm(initial={'course': course.id if course else None})
    
    # Obtener cursos del tutor
    courses = Course.objects.filter(
        institution=institution,
        teaching_assignments__tutor=request.user,
        teaching_assignments__status='active'
    ).distinct()
    
    # Si es admin o institución, puede crear en cualquier curso
    if UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        courses = Course.objects.filter(institution=institution)
    
    context = {
        'institution': institution,
        'form': form,
        'courses': courses,
        'selected_course': course,
    }
    return render(request, 'editor/activity/tutor/activity_form.html', context)


@login_required
def tutor_activity_edit(request, institution_slug, activity_id):
    """Editar actividad existente"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    activity = get_object_or_404(Activity, id=activity_id)
    
    # Verificar que pertenece a la institución
    if activity.institution != institution:
        messages.error(request, 'No tienes permisos para editar esta actividad.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    # Verificar permisos
    if not TeachingAssignment.objects.filter(
        course=activity.course,
        tutor=request.user,
        status='active'
    ).exists() and not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para editar esta actividad.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    if request.method == 'POST':
        form = ActivityForm(request.POST, instance=activity)
        if form.is_valid():
            activity = form.save(commit=False)
            
            # Si se publica por primera vez, guardar fecha de publicación
            if activity.status == 'published' and not activity.published_at:
                activity.published_at = timezone.now()
            
            activity.save()
            messages.success(request, f'Actividad "{activity.title}" actualizada exitosamente.')
            return redirect('editor:tutor_activities_list', institution_slug=institution_slug, course_id=activity.course.id)
    else:
        form = ActivityForm(instance=activity)
    
    context = {
        'institution': institution,
        'activity': activity,
        'form': form,
        'action': 'Editar',
    }
    return render(request, 'editor/activity/tutor/activity_form.html', context)


@login_required
@require_POST
def tutor_activity_publish(request, institution_slug, activity_id):
    """Publicar una actividad"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    activity = get_object_or_404(Activity, id=activity_id)
    
    # Verificar que pertenece a la institución
    if activity.institution != institution:
        messages.error(request, 'No tienes permisos para publicar esta actividad.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    # Verificar permisos
    if not TeachingAssignment.objects.filter(
        course=activity.course,
        tutor=request.user,
        status='active'
    ).exists() and not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para publicar esta actividad.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    if activity.status == 'draft':
        activity.status = 'published'
        if not activity.published_at:
            activity.published_at = timezone.now()
        activity.save()
        messages.success(request, f'Actividad "{activity.title}" publicada exitosamente.')
    else:
        messages.warning(request, 'La actividad ya está publicada o cerrada.')
    
    return redirect('editor:tutor_activities_list', institution_slug=institution_slug, course_id=activity.course.id)


@login_required
def tutor_activity_submissions(request, institution_slug, activity_id):
    """Lista de entregas de una actividad (vista de tutor)"""
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
        messages.error(request, 'No tienes permisos para ver las entregas de esta actividad.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    submissions = Submission.objects.filter(
        activity=activity
    ).select_related('student').order_by('-submitted_at', 'student__last_name', 'student__first_name')
    
    context = {
        'institution': institution,
        'activity': activity,
        'submissions': submissions,
    }
    return render(request, 'editor/activity/tutor/activity_submissions.html', context)


@login_required
def tutor_submission_grade(request, institution_slug, submission_id):
    """Calificar una entrega"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    submission = get_object_or_404(Submission, id=submission_id)
    activity = submission.activity
    
    # Verificar que pertenece a la institución
    if activity.institution != institution:
        messages.error(request, 'No tienes permisos para calificar esta entrega.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    # Verificar permisos
    if not TeachingAssignment.objects.filter(
        course=activity.course,
        tutor=request.user,
        status='active'
    ).exists() and not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para calificar esta entrega.')
        return redirect('editor:tutor_courses_list', institution_slug=institution_slug)
    
    # Obtener feedback existente o crear uno nuevo
    feedback = submission.get_latest_feedback()
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST, instance=feedback, submission=submission, tutor=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entrega calificada exitosamente.')
            return redirect('editor:tutor_activity_submissions', institution_slug=institution_slug, activity_id=activity.id)
    else:
        form = FeedbackForm(instance=feedback, submission=submission, tutor=request.user)
    
    context = {
        'institution': institution,
        'activity': activity,
        'submission': submission,
        'form': form,
        'feedback': feedback,
        'rubric': activity.rubric if hasattr(activity, 'rubric') else None,
    }
    return render(request, 'editor/activity/tutor/submission_grade.html', context)


# ============================================
# VISTAS DE ESTUDIANTE
# ============================================

@login_required
def student_activities_list(request, institution_slug, course_id):
    """Lista de actividades de un curso (vista de estudiante)"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    course = get_object_or_404(Course, id=course_id, institution=institution)
    
    # Verificar que el estudiante está matriculado en el curso
    if not Enrollment.objects.filter(
        course=course,
        student=request.user,
        status='active'
    ).exists() and not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No estás matriculado en este curso.')
        return redirect('editor:student_courses_list', institution_slug=institution_slug)
    
    # Solo actividades publicadas con sus entregas
    activities_with_submissions = []
    activities = Activity.objects.filter(
        course=course,
        status='published'
    ).order_by('-deadline', '-created_at')
    
    for activity in activities:
        submission = Submission.objects.filter(
            activity=activity,
            student=request.user
        ).order_by('-attempt').first()
        activities_with_submissions.append({
            'activity': activity,
            'submission': submission
        })
    
    context = {
        'institution': institution,
        'course': course,
        'activities_with_submissions': activities_with_submissions,
    }
    return render(request, 'editor/activity/student/activities_list.html', context)


@login_required
def student_activity_detail(request, institution_slug, activity_id):
    """Detalle de una actividad (vista de estudiante)"""
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
    
    # Obtener entrega del estudiante
    submission = Submission.objects.filter(
        activity=activity,
        student=request.user
    ).order_by('-attempt').first()
    
    # Obtener feedback si existe
    feedback = None
    if submission:
        feedback = submission.get_latest_feedback()
    
    context = {
        'institution': institution,
        'activity': activity,
        'submission': submission,
        'feedback': feedback,
        'can_submit': activity.is_published() and not activity.is_closed() and not activity.is_deadline_passed(),
    }
    return render(request, 'editor/activity/student/activity_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def student_activity_submit(request, institution_slug, activity_id):
    """Entregar una actividad"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    activity = get_object_or_404(Activity, id=activity_id, status='published')
    
    # Verificar que pertenece a la institución
    if activity.institution != institution:
        messages.error(request, 'No tienes permisos para entregar esta actividad.')
        return redirect('editor:student_courses_list', institution_slug=institution_slug)
    
    # Verificar que el estudiante está matriculado en el curso
    if not Enrollment.objects.filter(
        course=activity.course,
        student=request.user,
        status='active'
    ).exists():
        messages.error(request, 'No estás matriculado en este curso.')
        return redirect('editor:student_courses_list', institution_slug=institution_slug)
    
    # Validaciones
    if activity.is_closed():
        messages.error(request, 'La actividad está cerrada.')
        return redirect('editor:student_activity_detail', institution_slug=institution_slug, activity_id=activity_id)
    
    if activity.is_deadline_passed():
        messages.error(request, 'La fecha límite ya pasó.')
        return redirect('editor:student_activity_detail', institution_slug=institution_slug, activity_id=activity_id)
    
    # Obtener última entrega
    last_submission = Submission.objects.filter(
        activity=activity,
        student=request.user
    ).order_by('-attempt').first()
    
    # Verificar re-entrega
    if last_submission and last_submission.status in ['submitted', 'graded']:
        if not activity.allow_resubmit:
            messages.error(request, 'No se permite re-entrega para esta actividad.')
            return redirect('editor:student_activity_detail', institution_slug=institution_slug, activity_id=activity_id)
    
    if request.method == 'POST':
        # Obtener project_id del request (puede venir de un formulario o AJAX)
        project_id = request.POST.get('project_id') or request.GET.get('project_id')
        if not project_id:
            messages.error(request, 'Debes seleccionar un proyecto para entregar.')
            return redirect('editor:student_activity_detail', institution_slug=institution_slug, activity_id=activity_id)
        
        # Verificar que el proyecto pertenece al estudiante
        try:
            from .models import IDEProject
            project = IDEProject.objects.get(id=project_id, owner=request.user)
        except IDEProject.DoesNotExist:
            # Intentar con Project legacy
            from .models import Project
            try:
                project = Project.objects.get(id=project_id, student__user=request.user)
                # Convertir a IDEProject si es necesario
                project = IDEProject.objects.create(
                    owner=request.user,
                    institution=institution,
                    name=project.name,
                    blockly_xml=project.xml_content or '',
                    arduino_code=project.arduino_code or ''
                )
            except Project.DoesNotExist:
                messages.error(request, 'No tienes permisos para entregar este proyecto.')
                return redirect('editor:student_activity_detail', institution_slug=institution_slug, activity_id=activity_id)
        
        # Crear artifact_ref
        artifact_ref = {
            'project_id': str(project.id),
            'submitted_at': timezone.now().isoformat(),
        }
        
        # Obtener el contenido actual del proyecto
        artifact_ref['blockly_xml'] = project.blockly_xml
        artifact_ref['arduino_code'] = project.arduino_code
        
        # Crear entrega con transacción para evitar doble submit
        with transaction.atomic():
            # Obtener el siguiente intento
            if last_submission:
                next_attempt = last_submission.attempt + 1
            else:
                next_attempt = 1
            
            # Verificar que no existe ya una entrega con este intento
            if Submission.objects.filter(
                activity=activity,
                student=request.user,
                attempt=next_attempt
            ).exists():
                messages.error(request, 'Ya existe una entrega con este intento. Por favor, recarga la página.')
                return redirect('editor:student_activity_detail', institution_slug=institution_slug, activity_id=activity_id)
            
            submission = Submission.objects.create(
                activity=activity,
                student=request.user,
                attempt=next_attempt,
                artifact_ref=artifact_ref,
                status='submitted',
                submitted_at=timezone.now()
            )
            
            # Congelar workspace si no se permite re-entrega
            from .models import ActivityWorkspace
            if not activity.allow_resubmit:
                workspace = ActivityWorkspace.objects.filter(
                    activity=activity,
                    student=request.user
                ).first()
                if workspace:
                    workspace.freeze()
        
        messages.success(request, f'Actividad entregada exitosamente (Intento {submission.attempt}).')
        return redirect('editor:student_activity_detail', institution_slug=institution_slug, activity_id=activity_id)
    
    # GET: Mostrar formulario de confirmación
    context = {
        'institution': institution,
        'activity': activity,
        'last_submission': last_submission,
    }
    return render(request, 'editor/activity/student/activity_submit.html', context)


@login_required
def student_submission_feedback(request, institution_slug, submission_id):
    """Ver feedback de una entrega"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Verificar que pertenece al estudiante
    if submission.student != request.user:
        messages.error(request, 'No tienes permisos para ver esta entrega.')
        return redirect('editor:student_courses_list', institution_slug=institution_slug)
    
    # Verificar que pertenece a la institución
    if submission.institution != institution:
        messages.error(request, 'No tienes permisos para ver esta entrega.')
        return redirect('editor:student_courses_list', institution_slug=institution_slug)
    
    feedback = submission.get_latest_feedback()
    
    context = {
        'institution': institution,
        'submission': submission,
        'activity': submission.activity,
        'feedback': feedback,
        'rubric': submission.activity.rubric if hasattr(submission.activity, 'rubric') else None,
    }
    return render(request, 'editor/activity/student/submission_feedback.html', context)


# ============================================
# APIs DE ESTADO (P3.1)
# ============================================

@login_required
@require_http_methods(["GET"])
def api_submission_status(request, institution_slug, activity_id):
    """
    API para obtener el estado de submission del estudiante actual.
    GET /api/activities/<activity_id>/my-submission-status/
    """
    try:
        institution = get_object_or_404(Institution, slug=institution_slug, status='active')
        activity = get_object_or_404(Activity, id=activity_id)
        
        # Verificar que la actividad pertenece a la institución
        if activity.institution != institution:
            return JsonResponse({'error': 'Actividad no encontrada'}, status=404)
        
        # Verificar que el estudiante está matriculado
        is_enrolled = Enrollment.objects.filter(
            course=activity.course,
            student=request.user,
            status='active'
        ).exists()
        
        is_admin = UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution)
        
        if not is_enrolled and not is_admin:
            return JsonResponse({'error': 'No tienes acceso a esta actividad'}, status=403)
        
        # Obtener última submission
        submission = Submission.objects.filter(
            activity=activity,
            student=request.user
        ).order_by('-attempt').first()
        
        # Determinar estado
        if submission:
            status = submission.status  # pending, submitted, graded
            submitted_at = submission.submitted_at.isoformat() if submission.submitted_at else None
            attempt = submission.attempt
        else:
            status = 'in_progress'
            submitted_at = None
            attempt = 0
        
        # Determinar si puede entregar
        can_deliver = (
            activity.status == 'published' and
            not activity.is_closed() and
            not activity.is_deadline_passed() and
            (
                not submission or 
                submission.status == 'pending' or
                (submission.status in ['submitted', 'graded'] and activity.allow_resubmit)
            )
        )
        
        # Determinar si es solo lectura
        is_readonly = (
            activity.is_closed() or
            activity.is_deadline_passed() or
            (submission and submission.status in ['submitted', 'graded'] and not activity.allow_resubmit)
        )
        
        return JsonResponse({
            'status': status,
            'submitted_at': submitted_at,
            'attempt': attempt,
            'can_deliver': can_deliver,
            'is_readonly': is_readonly,
            'allow_resubmit': activity.allow_resubmit,
            'deadline': activity.deadline.isoformat() if activity.deadline else None,
            'is_deadline_passed': activity.is_deadline_passed(),
            'activity_status': activity.status,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
