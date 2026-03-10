"""
Vistas del Módulo 5: Agent Local Institucional (Monitoreo y Control)
NO modifica la lógica de compilación ni subida del Agent existente
"""
import platform
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Institution, AgentInstance
from .models import UserRoleHelper


# ============================================
# APIs PARA EL AGENT (sin autenticación de usuario, solo token)
# ============================================

@csrf_exempt
@require_POST
def api_agent_register(request):
    """
    API para que el Agent se registre
    El Agent envía su información y obtiene su ID
    """
    try:
        data = json.loads(request.body)
        
        # Verificar token institucional
        institution_token = data.get('institution_token') or request.headers.get('X-Institution-Token')
        if not institution_token:
            return JsonResponse({'ok': False, 'error': 'Token institucional requerido'}, status=400)
        
        # Buscar institución por token (por ahora usamos slug o code)
        # TODO: Implementar tokens reales si es necesario
        institution = None
        try:
            # Intentar por slug primero
            institution = Institution.objects.filter(slug=institution_token, status='active').first()
            if not institution:
                # Intentar por code
                institution = Institution.objects.filter(code=institution_token, status='active').first()
        except Exception:
            pass
        
        if not institution:
            return JsonResponse({'ok': False, 'error': 'Token institucional inválido'}, status=403)
        
        # Obtener información del Agent
        hostname = data.get('hostname', platform.node())
        os_info = data.get('os', platform.system())
        agent_version = data.get('agent_version', '1.0.0')
        ide_version_compatible = data.get('ide_version_compatible', '')
        
        # Metadata adicional
        meta = data.get('meta', {})
        meta['python_version'] = platform.python_version()
        meta['platform'] = platform.platform()
        
        # Crear o actualizar instancia del Agent
        agent_instance, created = AgentInstance.objects.get_or_create(
            institution=institution,
            hostname=hostname,
            defaults={
                'os': os_info,
                'agent_version': agent_version,
                'ide_version_compatible': ide_version_compatible,
                'status': 'online',
                'last_seen': timezone.now(),
                'meta': meta,
            }
        )
        
        if not created:
            # Actualizar información si ya existe
            agent_instance.os = os_info
            agent_instance.agent_version = agent_version
            agent_instance.ide_version_compatible = ide_version_compatible
            agent_instance.meta.update(meta)
            agent_instance.update_heartbeat()
        
        return JsonResponse({
            'ok': True,
            'agent_id': str(agent_instance.id),
            'message': 'Agent registrado exitosamente' if created else 'Agent actualizado',
            'institution': {
                'id': str(institution.id),
                'name': institution.name,
                'slug': institution.slug,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def api_agent_heartbeat(request):
    """
    API para que el Agent envíe heartbeat periódicamente
    Mantiene el estado ONLINE y actualiza last_seen
    """
    try:
        data = json.loads(request.body)
        agent_id = data.get('agent_id') or request.headers.get('X-Agent-ID')
        
        if not agent_id:
            return JsonResponse({'ok': False, 'error': 'agent_id requerido'}, status=400)
        
        try:
            agent_instance = AgentInstance.objects.get(id=agent_id)
        except AgentInstance.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Agent no encontrado'}, status=404)
        
        # Actualizar heartbeat
        agent_instance.update_heartbeat()
        
        # Opcionalmente actualizar metadata
        if 'meta' in data:
            agent_instance.meta.update(data['meta'])
            agent_instance.save(update_fields=['meta'])
        
        return JsonResponse({
            'ok': True,
            'message': 'Heartbeat recibido',
            'status': agent_instance.status,
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_agent_list(request):
    """
    API para listar Agents
    - Admin: todos los Agents
    - Institución: solo sus Agents
    """
    try:
        institution_slug = request.GET.get('institution')
        
        if institution_slug:
            # Listar Agents de una institución específica
            institution = get_object_or_404(Institution, slug=institution_slug, status='active')
            agents = AgentInstance.objects.filter(institution=institution)
        elif request.user.is_superuser or request.user.is_staff:
            # Admin: todos los Agents
            agents = AgentInstance.objects.all()
        else:
            # Usuario autenticado: Agents de sus instituciones
            institutions = UserRoleHelper.get_user_institutions(request.user)
            agents = AgentInstance.objects.filter(institution__in=institutions)
        
        # Actualizar estado basado en last_seen
        for agent in agents:
            if not agent.is_online() and agent.status == 'online':
                agent.mark_offline()
        
        agents_list = [agent.get_info() for agent in agents]
        
        return JsonResponse({
            'ok': True,
            'agents': agents_list,
            'count': len(agents_list),
        })
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_agent_status(request, agent_id):
    """
    API para obtener estado de un Agent específico
    """
    try:
        agent = get_object_or_404(AgentInstance, id=agent_id)
        
        # Verificar permisos
        if not request.user.is_superuser and not request.user.is_staff:
            # Verificar que el usuario pertenece a la institución del Agent
            if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], agent.institution):
                return JsonResponse({'ok': False, 'error': 'No tienes permisos para ver este Agent'}, status=403)
        
        # Actualizar estado basado en last_seen
        is_online = agent.is_online()
        
        return JsonResponse({
            'ok': True,
            'agent': agent.get_info(),
            'is_online': is_online,
        })
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


# ============================================
# VISTAS DE ADMINISTRACIÓN
# ============================================

@login_required
def admin_agents_list(request):
    """Lista global de Agents (vista de admin)"""
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('editor:dashboard')
    
    # Actualizar estados offline basados en last_seen
    agents = AgentInstance.objects.all()
    for agent in agents:
        if not agent.is_online() and agent.status == 'online':
            agent.mark_offline()
    
    agents = AgentInstance.objects.all().select_related('institution').order_by('-last_seen', '-created_at')
    
    # Estadísticas
    total_agents = agents.count()
    online_agents = agents.filter(status='online').count()
    offline_agents = agents.filter(status='offline').count()
    error_agents = agents.filter(status='error').count()
    
    context = {
        'agents': agents,
        'total_agents': total_agents,
        'online_agents': online_agents,
        'offline_agents': offline_agents,
        'error_agents': error_agents,
    }
    return render(request, 'editor/agent/admin/agents_list.html', context)


@login_required
def admin_agent_detail(request, agent_id):
    """Detalle de un Agent (vista de admin)"""
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('editor:dashboard')
    
    agent = get_object_or_404(AgentInstance, id=agent_id)
    
    # Verificar si está online
    is_online = agent.is_online()
    if not is_online and agent.status == 'online':
        agent.mark_offline()
    
    context = {
        'agent': agent,
        'is_online': is_online,
    }
    return render(request, 'editor/agent/admin/agent_detail.html', context)


# ============================================
# VISTAS DE INSTITUCIÓN
# ============================================

@login_required
def institution_agents_list(request, institution_slug):
    """Lista de Agents de la institución"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para ver los Agents.')
        return redirect('editor:dashboard')
    
    # Actualizar estados offline basados en last_seen
    agents = AgentInstance.objects.filter(institution=institution)
    for agent in agents:
        if not agent.is_online() and agent.status == 'online':
            agent.mark_offline()
    
    agents = AgentInstance.objects.filter(institution=institution).order_by('-last_seen', '-created_at')
    
    # Estadísticas
    total_agents = agents.count()
    online_agents = agents.filter(status='online').count()
    offline_agents = agents.filter(status='offline').count()
    error_agents = agents.filter(status='error').count()
    
    context = {
        'institution': institution,
        'agents': agents,
        'total_agents': total_agents,
        'online_agents': online_agents,
        'offline_agents': offline_agents,
        'error_agents': error_agents,
    }
    return render(request, 'editor/agent/institution/agents_list.html', context)


@login_required
def institution_agent_detail(request, institution_slug, agent_id):
    """Detalle de un Agent de la institución"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    agent = get_object_or_404(AgentInstance, id=agent_id, institution=institution)
    
    # Verificar permisos
    if not UserRoleHelper.user_has_role(request.user, ['admin', 'institution'], institution):
        messages.error(request, 'No tienes permisos para ver este Agent.')
        return redirect('editor:institution_agents_list', institution_slug=institution_slug)
    
    # Verificar si está online
    is_online = agent.is_online()
    if not is_online and agent.status == 'online':
        agent.mark_offline()
    
    context = {
        'institution': institution,
        'agent': agent,
        'is_online': is_online,
    }
    return render(request, 'editor/agent/institution/agent_detail.html', context)


# ============================================
# API PARA VERIFICAR AGENT DESDE EL IDE
# ============================================

@login_required
def api_agent_check(request):
    """
    API para verificar estado del Agent desde el IDE
    Retorna el estado del Agent para mostrar en el IDE
    """
    try:
        institution_slug = request.GET.get('institution')
        
        if not institution_slug:
            return JsonResponse({
                'ok': False,
                'agent_online': False,
                'message': 'No se especificó institución'
            })
        
        institution = get_object_or_404(Institution, slug=institution_slug, status='active')
        
        # Buscar Agents online de la institución
        agents = AgentInstance.objects.filter(
            institution=institution,
            status='online'
        ).order_by('-last_seen')
        
        # Verificar que estén realmente online
        online_agents = []
        for agent in agents:
            if agent.is_online():
                online_agents.append(agent)
        
        if online_agents:
            latest_agent = online_agents[0]
            return JsonResponse({
                'ok': True,
                'agent_online': True,
                'agent': {
                    'id': str(latest_agent.id),
                    'hostname': latest_agent.hostname,
                    'version': latest_agent.agent_version,
                    'last_seen': latest_agent.last_seen.isoformat(),
                },
                'message': 'Agent disponible'
            })
        else:
            return JsonResponse({
                'ok': True,
                'agent_online': False,
                'message': 'No hay Agents online disponibles',
                'hint': 'Verifica que el Agent esté ejecutándose en tu PC'
            })
            
    except Institution.DoesNotExist:
        return JsonResponse({
            'ok': False,
            'agent_online': False,
            'message': 'Institución no encontrada'
        })
    except Exception as e:
        return JsonResponse({
            'ok': False,
            'agent_online': False,
            'message': f'Error al verificar Agent: {str(e)}'
        })
