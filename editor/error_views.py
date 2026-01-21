"""
Vistas del Módulo 6: Observabilidad (ErrorEvent/AuditLog) + dashboards por rol
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
import json

from .models import Institution, ErrorEvent, AuditLog, Course, Activity, UserRoleHelper
from .mixins import InstitutionScopedMixin, RoleRequiredMixin


# ============================================
# API ENDPOINTS PARA ERRORES
# ============================================

@csrf_exempt
@require_POST
def api_error_create(request):
    """
    API para registrar eventos de error desde el frontend (IDE y dashboards)
    POST /api/errors/
    """
    try:
        data = json.loads(request.body)
        
        # Obtener institución (del request o del usuario)
        institution = None
        if hasattr(request, 'current_institution'):
            institution = request.current_institution
        elif request.user.is_authenticated:
            # Si no hay current_institution, usar la del usuario
            institutions = UserRoleHelper.get_user_institutions(request.user)
            if institutions.count() == 1:
                institution = institutions.first()
        
        # Datos del error
        code = data.get('code', 'GenericError')
        severity = data.get('severity', 'medium')
        message = data.get('message', 'Error sin descripción')
        context = data.get('context', {})
        
        # Validar código
        valid_codes = [choice[0] for choice in ErrorEvent.ERROR_CODE_CHOICES]
        if code not in valid_codes:
            code = 'GenericError'
        
        # Validar severidad
        valid_severities = [choice[0] for choice in ErrorEvent.SEVERITY_CHOICES]
        if severity not in valid_severities:
            severity = 'medium'
        
        # Crear ErrorEvent
        error_event = ErrorEvent.objects.create(
            institution=institution,
            user=request.user if request.user.is_authenticated else None,
            code=code,
            severity=severity,
            message=message,
            context=context,
        )
        
        return JsonResponse({
            'ok': True,
            'error_id': str(error_event.id),
            'message': 'Error registrado exitosamente',
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@require_GET
def api_error_list(request):
    """
    API para listar errores filtrados por rol/tenant
    GET /api/errors/
    """
    user = request.user
    institution = getattr(request, 'current_institution', None)
    
    # Determinar qué errores puede ver el usuario
    errors = ErrorEvent.objects.all()
    
    # Admin: ve todos
    if user.is_superuser:
        pass  # Ya tiene todos
    # Institución: ve solo su institución
    elif UserRoleHelper.user_has_role(user, 'institution', institution):
        errors = errors.filter(institution=institution)
    # Tutor: ve errores de sus cursos/actividades
    elif UserRoleHelper.user_has_role(user, 'tutor', institution):
        # Obtener cursos donde es tutor
        courses = Course.objects.filter(tutor=user, institution=institution)
        # Obtener actividades de esos cursos
        activity_ids = Activity.objects.filter(course__in=courses).values_list('id', flat=True)
        # Filtrar errores relacionados con esas actividades
        # Por ahora, filtramos por institución y usuario
        errors = errors.filter(
            Q(institution=institution) &
            (Q(user=user) | Q(context__course_id__in=[str(c.id) for c in courses]))
        )
    # Estudiante: solo diagnóstico propio
    elif UserRoleHelper.user_has_role(user, 'student', institution):
        errors = errors.filter(user=user, institution=institution)
    else:
        errors = ErrorEvent.objects.none()
    
    # Filtros opcionales
    code_filter = request.GET.get('code')
    if code_filter:
        errors = errors.filter(code=code_filter)
    
    severity_filter = request.GET.get('severity')
    if severity_filter:
        errors = errors.filter(severity=severity_filter)
    
    resolved_filter = request.GET.get('resolved')
    if resolved_filter == 'true':
        errors = errors.filter(resolved=True)
    elif resolved_filter == 'false':
        errors = errors.filter(resolved=False)
    
    # Paginación
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    paginator = Paginator(errors.order_by('-ts'), per_page)
    page_obj = paginator.get_page(page)
    
    # Serializar
    errors_data = [{
        'id': str(e.id),
        'code': e.code,
        'severity': e.severity,
        'message': e.message,
        'context': e.context,
        'ts': e.ts.isoformat(),
        'resolved': e.resolved,
        'user': e.user.username if e.user else None,
        'institution': e.institution.name if e.institution else None,
    } for e in page_obj]
    
    return JsonResponse({
        'ok': True,
        'errors': errors_data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': paginator.count,
            'pages': paginator.num_pages,
        }
    })


# ============================================
# VISTAS DE DASHBOARDS (Templates)
# ============================================

@login_required
def admin_errors_list(request):
    """
    Dashboard de errores para Admin (global)
    /admin-panel/errors/
    """
    if not request.user.is_superuser:
        messages.error(request, "Acceso denegado")
        return redirect('editor:dashboard_redirect')
    
    errors = ErrorEvent.objects.all().order_by('-ts')
    
    # Filtros
    code_filter = request.GET.get('code')
    if code_filter:
        errors = errors.filter(code=code_filter)
    
    severity_filter = request.GET.get('severity')
    if severity_filter:
        errors = errors.filter(severity=severity_filter)
    
    resolved_filter = request.GET.get('resolved')
    if resolved_filter == 'true':
        errors = errors.filter(resolved=True)
    elif resolved_filter == 'false':
        errors = errors.filter(resolved=False)
    
    # Estadísticas
    stats = {
        'total': errors.count(),
        'resolved': errors.filter(resolved=True).count(),
        'unresolved': errors.filter(resolved=False).count(),
        'by_severity': errors.values('severity').annotate(count=Count('id')),
        'by_code': errors.values('code').annotate(count=Count('id')).order_by('-count')[:10],
    }
    
    # Paginación
    paginator = Paginator(errors, 50)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    context = {
        'errors': page_obj,
        'stats': stats,
        'error_codes': ErrorEvent.ERROR_CODE_CHOICES,
        'severities': ErrorEvent.SEVERITY_CHOICES,
        'code_filter': code_filter,
        'severity_filter': severity_filter,
        'resolved_filter': resolved_filter,
    }
    
    return render(request, 'editor/error/admin/errors_list.html', context)


@login_required
def admin_error_detail(request, error_id):
    """
    Detalle de error para Admin
    /admin-panel/errors/<id>/
    """
    if not request.user.is_superuser:
        messages.error(request, "Acceso denegado")
        return redirect('editor:dashboard_redirect')
    
    error = get_object_or_404(ErrorEvent, id=error_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'resolve':
            error.mark_resolved(request.user)
            messages.success(request, "Error marcado como resuelto")
            return redirect('editor:admin_error_detail', error_id=error_id)
        elif action == 'unresolve':
            error.resolved = False
            error.resolved_at = None
            error.resolved_by = None
            error.save()
            messages.success(request, "Error marcado como no resuelto")
            return redirect('editor:admin_error_detail', error_id=error_id)
    
    context = {
        'error': error,
    }
    
    return render(request, 'editor/error/admin/error_detail.html', context)


@login_required
def institution_errors_list(request, institution_slug):
    """
    Dashboard de errores para Institución
    /i/<slug>/institution/errors/
    """
    institution = get_object_or_404(Institution, slug=institution_slug)
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, "Acceso denegado")
        return redirect('editor:dashboard_redirect')
    
    # Filtrar por institución
    errors = ErrorEvent.objects.filter(institution=institution).order_by('-ts')
    
    # Filtros
    code_filter = request.GET.get('code')
    if code_filter:
        errors = errors.filter(code=code_filter)
    
    severity_filter = request.GET.get('severity')
    if severity_filter:
        errors = errors.filter(severity=severity_filter)
    
    resolved_filter = request.GET.get('resolved')
    if resolved_filter == 'true':
        errors = errors.filter(resolved=True)
    elif resolved_filter == 'false':
        errors = errors.filter(resolved=False)
    
    # Agrupación por código
    by_code = errors.values('code').annotate(
        count=Count('id'),
        unresolved=Count('id', filter=Q(resolved=False)),
    ).order_by('-count')
    
    # Estadísticas
    stats = {
        'total': errors.count(),
        'resolved': errors.filter(resolved=True).count(),
        'unresolved': errors.filter(resolved=False).count(),
        'by_severity': errors.values('severity').annotate(count=Count('id')),
        'by_code': by_code[:10],
        'recent_24h': errors.filter(ts__gte=timezone.now() - timedelta(hours=24)).count(),
    }
    
    # Paginación
    paginator = Paginator(errors, 50)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    context = {
        'errors': page_obj,
        'stats': stats,
        'error_codes': ErrorEvent.ERROR_CODE_CHOICES,
        'severities': ErrorEvent.SEVERITY_CHOICES,
        'code_filter': code_filter,
        'severity_filter': severity_filter,
        'resolved_filter': resolved_filter,
        'institution': institution,
    }
    
    return render(request, 'editor/error/institution/errors_list.html', context)


@login_required
def tutor_errors_list(request, institution_slug):
    """
    Dashboard de errores para Tutor (solo cursos donde enseña)
    /i/<slug>/tutor/errors/
    """
    institution = get_object_or_404(Institution, slug=institution_slug)
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'tutor'], institution):
        messages.error(request, "Acceso denegado")
        return redirect('editor:dashboard_redirect')
    
    # Obtener cursos donde es tutor
    courses = Course.objects.filter(tutor=request.user, institution=institution)
    activity_ids = Activity.objects.filter(course__in=courses).values_list('id', flat=True)
    
    # Filtrar errores relacionados
    errors = ErrorEvent.objects.filter(
        Q(institution=institution) &
        (
            Q(user=request.user) |
            Q(context__course_id__in=[str(c.id) for c in courses]) |
            Q(context__activity_id__in=[str(aid) for aid in activity_ids])
        )
    ).order_by('-ts')
    
    # Filtros
    code_filter = request.GET.get('code')
    if code_filter:
        errors = errors.filter(code=code_filter)
    
    severity_filter = request.GET.get('severity')
    if severity_filter:
        errors = errors.filter(severity=severity_filter)
    
    # Estadísticas básicas
    stats = {
        'total': errors.count(),
        'unresolved': errors.filter(resolved=False).count(),
        'by_code': errors.values('code').annotate(count=Count('id')).order_by('-count')[:5],
    }
    
    # Paginación
    paginator = Paginator(errors, 50)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    context = {
        'errors': page_obj,
        'stats': stats,
        'error_codes': ErrorEvent.ERROR_CODE_CHOICES,
        'severities': ErrorEvent.SEVERITY_CHOICES,
        'code_filter': code_filter,
        'severity_filter': severity_filter,
        'institution': institution,
        'courses': courses,
    }
    
    return render(request, 'editor/error/tutor/errors_list.html', context)


# ============================================
# HELPER PARA CREAR AUDIT LOG
# ============================================

def create_audit_log(actor, action, entity, entity_id=None, institution=None, metadata=None):
    """
    Helper para crear logs de auditoría
    """
    return AuditLog.objects.create(
        actor=actor,
        institution=institution,
        action=action,
        entity=entity,
        entity_id=str(entity_id) if entity_id else None,
        metadata=metadata or {},
    )
