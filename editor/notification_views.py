"""
API de Notificaciones - Listar, marcar como leídas, y crear notificaciones.
Las notificaciones se crean cuando ocurren eventos (nueva actividad, calificación, etc.)
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone

from .models import Notification, Activity, Student


def notify_students_of_new_activity(activity, institution, notification_type='activity_new'):
    """
    Crea notificaciones para todos los estudiantes del grupo cuando el tutor
    crea o publica una actividad.
    """
    if not activity.group:
        return
    students = Student.objects.filter(
        group=activity.group,
        is_active=True
    ).select_related('user')
    link_url = f'/i/{institution.slug}/student/activities/{activity.id}/'
    title = f'Nueva actividad: {activity.title}' if notification_type == 'activity_new' else f'Actividad publicada: {activity.title}'
    message = activity.objective or activity.instructions[:100] if activity.instructions else ''
    for student in students:
        Notification.objects.create(
            user=student.user,
            institution=institution,
            notification_type=notification_type,
            title=title,
            message=message,
            link_url=link_url,
        )


@login_required
@require_GET
def api_notifications_list(request):
    """Lista las notificaciones del usuario (últimas 30)"""
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:30]

    data = {
        'ok': True,
        'notifications': [
            {
                'id': str(n.id),
                'title': n.title,
                'message': n.message,
                'type': n.notification_type,
                'link_url': n.link_url or '',
                'read': n.read,
                'created_at': n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ],
        'unread_count': Notification.objects.filter(user=request.user, read=False).count(),
    }
    return JsonResponse(data)


@login_required
@require_POST
def api_notifications_mark_read(request, notification_id):
    """Marca una notificación como leída"""
    try:
        n = Notification.objects.get(id=notification_id, user=request.user)
        n.mark_as_read()
        return JsonResponse({'ok': True})
    except Notification.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'No encontrada'}, status=404)


@login_required
@require_POST
def api_notifications_mark_all_read(request):
    """Marca todas las notificaciones del usuario como leídas"""
    updated = Notification.objects.filter(
        user=request.user,
        read=False
    ).update(read=True, read_at=timezone.now())
    return JsonResponse({'ok': True, 'updated': updated})
