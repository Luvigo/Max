"""
MÓDULO 4: Vistas de Grupos y Estudiantes

Tutor: CRUD grupos, crear estudiantes, asignar a grupos.
Estudiante: ver su contexto (grupo/tutor/institución).
Admin: supervisa desde Django Admin (/admin/).
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.core.paginator import Paginator
import uuid

from .models import Institution, Membership, TutorProfile, StudentGroup, Student, Course
from .mixins import tutor_required, student_required


# ============================================
# VISTAS DE TUTOR: GRUPOS
# ============================================

@login_required
@tutor_required
def tutor_groups_list(request, institution_slug):
    """Lista de grupos del tutor"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Solo grupos del tutor en esta institución
    groups = StudentGroup.objects.filter(
        institution=institution,
        tutor=request.user
    ).order_by('-academic_year', 'name')
    
    # Filtros
    status_filter = request.GET.get('status', '')
    year_filter = request.GET.get('year', '')
    
    if status_filter:
        groups = groups.filter(status=status_filter)
    if year_filter:
        groups = groups.filter(academic_year=year_filter)
    
    # Paginación
    paginator = Paginator(groups, 10)
    page = request.GET.get('page')
    groups = paginator.get_page(page)
    
    # Años académicos para filtro
    academic_years = StudentGroup.objects.filter(
        institution=institution,
        tutor=request.user
    ).values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'groups': groups,
        'academic_years': academic_years,
        'status_filter': status_filter,
        'year_filter': year_filter,
    }
    
    return render(request, 'editor/tutor/groups_list.html', context)


@login_required
@tutor_required
def tutor_group_create(request, institution_slug):
    """Crear nuevo grupo"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        description = request.POST.get('description', '').strip()
        academic_year = request.POST.get('academic_year', '').strip()
        semester = request.POST.get('semester', '').strip()
        max_students = request.POST.get('max_students', 30)
        
        # Validaciones
        errors = []
        if not name:
            errors.append('El nombre del grupo es requerido.')
        if not code:
            errors.append('El código del grupo es requerido.')
        if not academic_year:
            errors.append('El año académico es requerido.')
        
        # Verificar código único
        if code and StudentGroup.objects.filter(institution=institution, code=code).exists():
            errors.append(f'Ya existe un grupo con el código "{code}" en esta institución.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                group = StudentGroup.objects.create(
                    institution=institution,
                    tutor=request.user,
                    name=name,
                    code=code,
                    description=description,
                    academic_year=academic_year,
                    semester=semester,
                    max_students=int(max_students),
                    created_by=request.user,
                    status='active'
                )
                messages.success(request, f'Grupo "{name}" creado exitosamente.')
                return redirect('editor:tutor_group_detail', institution_slug=institution_slug, group_id=group.id)
            except Exception as e:
                messages.error(request, f'Error al crear el grupo: {str(e)}')
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'current_year': '2026',  # Año actual
    }
    
    return render(request, 'editor/tutor/group_form.html', context)


@login_required
@tutor_required
def tutor_group_detail(request, institution_slug, group_id):
    """Detalle de un grupo"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    group = get_object_or_404(
        StudentGroup,
        id=group_id,
        institution=institution,
        tutor=request.user
    )
    
    # Estudiantes del grupo
    students = Student.objects.filter(group=group).select_related('user').order_by('user__last_name', 'user__first_name')
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'group': group,
        'students': students,
        'students_count': students.filter(is_active=True).count(),
    }
    
    return render(request, 'editor/tutor/group_detail.html', context)


@login_required
@tutor_required
def tutor_group_edit(request, institution_slug, group_id):
    """Editar grupo"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    group = get_object_or_404(
        StudentGroup,
        id=group_id,
        institution=institution,
        tutor=request.user
    )
    
    if request.method == 'POST':
        group.name = request.POST.get('name', group.name).strip()
        group.description = request.POST.get('description', '').strip()
        group.academic_year = request.POST.get('academic_year', group.academic_year).strip()
        group.semester = request.POST.get('semester', '').strip()
        group.max_students = int(request.POST.get('max_students', 30))
        group.status = request.POST.get('status', 'active')
        
        try:
            group.save()
            messages.success(request, f'Grupo "{group.name}" actualizado exitosamente.')
            return redirect('editor:tutor_group_detail', institution_slug=institution_slug, group_id=group.id)
        except Exception as e:
            messages.error(request, f'Error al actualizar el grupo: {str(e)}')
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'group': group,
        'edit_mode': True,
    }
    
    return render(request, 'editor/tutor/group_form.html', context)


@login_required
@tutor_required
def tutor_group_delete(request, institution_slug, group_id):
    """Eliminar/Archivar grupo"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    group = get_object_or_404(
        StudentGroup,
        id=group_id,
        institution=institution,
        tutor=request.user
    )
    
    if request.method == 'POST':
        action = request.POST.get('action', 'archive')
        
        if action == 'delete':
            # Solo eliminar si no tiene estudiantes
            if group.get_students_count() > 0:
                messages.error(request, 'No se puede eliminar un grupo con estudiantes asignados.')
            else:
                group.delete()
                messages.success(request, f'Grupo "{group.name}" eliminado.')
                return redirect('editor:tutor_groups_list', institution_slug=institution_slug)
        else:
            # Archivar
            group.status = 'archived'
            group.save()
            messages.success(request, f'Grupo "{group.name}" archivado.')
            return redirect('editor:tutor_groups_list', institution_slug=institution_slug)
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'group': group,
    }
    
    return render(request, 'editor/tutor/group_delete.html', context)


# ============================================
# VISTAS DE TUTOR: ESTUDIANTES
# ============================================

@login_required
@tutor_required
def tutor_students_list(request, institution_slug):
    """Lista de estudiantes del tutor"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Estudiantes asignados al tutor o en grupos del tutor
    students = Student.objects.filter(
        institution=institution
    ).filter(
        # Asignados directamente al tutor o en sus grupos
        models.Q(tutor=request.user) | models.Q(group__tutor=request.user)
    ).select_related('user', 'group', 'course').distinct().order_by('user__last_name')
    
    # Filtros
    group_filter = request.GET.get('group', '')
    status_filter = request.GET.get('status', '')
    
    if group_filter:
        students = students.filter(group_id=group_filter)
    if status_filter == 'active':
        students = students.filter(is_active=True)
    elif status_filter == 'inactive':
        students = students.filter(is_active=False)
    
    # Paginación
    paginator = Paginator(students, 15)
    page = request.GET.get('page')
    students = paginator.get_page(page)
    
    # Grupos del tutor para filtro
    groups = StudentGroup.objects.filter(
        institution=institution,
        tutor=request.user,
        status='active'
    ).order_by('name')
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'students': students,
        'groups': groups,
        'group_filter': group_filter,
        'status_filter': status_filter,
    }
    
    return render(request, 'editor/tutor/students_list.html', context)


@login_required
@tutor_required
def tutor_student_create(request, institution_slug):
    """Crear nuevo estudiante"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Grupos del tutor
    groups = StudentGroup.objects.filter(
        institution=institution,
        tutor=request.user,
        status='active'
    ).order_by('name')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        student_id = request.POST.get('student_id', '').strip()
        group_id = request.POST.get('group', '')
        phone = request.POST.get('phone', '').strip()
        
        # Validaciones
        errors = []
        if not username:
            errors.append('El nombre de usuario es requerido.')
        if not email:
            errors.append('El email es requerido.')
        if not password:
            errors.append('La contraseña es requerida.')
        if not student_id:
            errors.append('El ID de estudiante es requerido.')
        
        # Verificar duplicados
        if username and User.objects.filter(username=username).exists():
            errors.append(f'Ya existe un usuario con el nombre "{username}".')
        if email and User.objects.filter(email=email).exists():
            errors.append(f'Ya existe un usuario con el email "{email}".')
        if student_id and Student.objects.filter(student_id=student_id).exists():
            errors.append(f'Ya existe un estudiante con el ID "{student_id}".')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                with transaction.atomic():
                    # Crear usuario
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name
                    )
                    
                    # Obtener grupo si se seleccionó
                    group = None
                    if group_id:
                        group = StudentGroup.objects.filter(
                            id=group_id,
                            institution=institution,
                            tutor=request.user
                        ).first()
                    
                    # Crear perfil de estudiante
                    student = Student.objects.create(
                        user=user,
                        student_id=student_id,
                        institution=institution,
                        group=group,
                        tutor=request.user,
                        phone=phone,
                        is_active=True,
                        created_by=request.user
                    )
                    
                    # Crear Membership
                    Membership.objects.create(
                        user=user,
                        institution=institution,
                        role='student',
                        is_active=True
                    )
                    
                    messages.success(request, f'Estudiante "{first_name} {last_name}" creado exitosamente.')
                    return redirect('editor:tutor_students_list', institution_slug=institution_slug)
                    
            except Exception as e:
                messages.error(request, f'Error al crear el estudiante: {str(e)}')
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'groups': groups,
    }
    
    return render(request, 'editor/tutor/student_create.html', context)


@login_required
@tutor_required
def tutor_student_detail(request, institution_slug, student_id):
    """Detalle de un estudiante"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Verificar que el estudiante pertenece al tutor
    from django.db.models import Q
    student = get_object_or_404(
        Student.objects.filter(
            Q(tutor=request.user) | Q(group__tutor=request.user)
        ),
        id=student_id,
        institution=institution
    )
    
    # Grupos del tutor para reasignación
    groups = StudentGroup.objects.filter(
        institution=institution,
        tutor=request.user,
        status='active'
    ).order_by('name')
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'student': student,
        'groups': groups,
    }
    
    return render(request, 'editor/tutor/student_detail.html', context)


@login_required
@tutor_required
def tutor_student_edit(request, institution_slug, student_id):
    """Editar estudiante"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    from django.db.models import Q
    student = get_object_or_404(
        Student.objects.filter(
            Q(tutor=request.user) | Q(group__tutor=request.user)
        ),
        id=student_id,
        institution=institution
    )
    
    groups = StudentGroup.objects.filter(
        institution=institution,
        tutor=request.user,
        status='active'
    ).order_by('name')
    
    if request.method == 'POST':
        # Actualizar datos del usuario
        student.user.first_name = request.POST.get('first_name', student.user.first_name).strip()
        student.user.last_name = request.POST.get('last_name', student.user.last_name).strip()
        student.user.email = request.POST.get('email', student.user.email).strip()
        student.user.save()
        
        # Actualizar datos del estudiante
        group_id = request.POST.get('group', '')
        if group_id:
            group = StudentGroup.objects.filter(
                id=group_id,
                institution=institution,
                tutor=request.user
            ).first()
            student.group = group
        else:
            student.group = None
        
        student.phone = request.POST.get('phone', '').strip()
        student.emergency_contact = request.POST.get('emergency_contact', '').strip()
        student.emergency_phone = request.POST.get('emergency_phone', '').strip()
        student.notes = request.POST.get('notes', '').strip()
        student.is_active = request.POST.get('is_active') == 'on'
        
        try:
            student.save()
            messages.success(request, f'Estudiante "{student.full_name}" actualizado exitosamente.')
            return redirect('editor:tutor_student_detail', institution_slug=institution_slug, student_id=student.id)
        except Exception as e:
            messages.error(request, f'Error al actualizar: {str(e)}')
    
    context = {
        'institution': institution,
        'user_role': 'tutor',
        'student': student,
        'groups': groups,
        'edit_mode': True,
    }
    
    return render(request, 'editor/tutor/student_edit.html', context)


@login_required
@tutor_required
def tutor_assign_student_to_group(request, institution_slug):
    """Asignar estudiante a grupo (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)
    
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    student_id = request.POST.get('student_id')
    group_id = request.POST.get('group_id')
    
    from django.db.models import Q
    
    try:
        student = Student.objects.filter(
            Q(tutor=request.user) | Q(group__tutor=request.user)
        ).get(id=student_id, institution=institution)
        
        if group_id:
            group = StudentGroup.objects.get(
                id=group_id,
                institution=institution,
                tutor=request.user
            )
            
            # Verificar capacidad
            if group.is_full():
                return JsonResponse({'ok': False, 'error': 'El grupo está lleno.'})
            
            student.group = group
        else:
            student.group = None
        
        student.save()
        
        return JsonResponse({
            'ok': True,
            'message': f'Estudiante asignado a {group.name if group_id else "sin grupo"}.'
        })
        
    except Student.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Estudiante no encontrado.'}, status=404)
    except StudentGroup.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Grupo no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


# ============================================
# VISTAS DE ESTUDIANTE: MI CONTEXTO
# ============================================

@login_required
@student_required
def student_my_context(request, institution_slug):
    """Vista del estudiante: su contexto (grupo, tutor, institución)"""
    institution = get_object_or_404(Institution, slug=institution_slug, status='active')
    
    # Obtener perfil del estudiante
    try:
        student = Student.objects.select_related(
            'user', 'institution', 'group', 'tutor', 'course'
        ).get(user=request.user, institution=institution)
    except Student.DoesNotExist:
        messages.error(request, 'No tienes un perfil de estudiante en esta institución.')
        return redirect('dashboard')
    
    # Obtener información del tutor
    tutor_info = None
    if student.get_tutor():
        tutor_user = student.get_tutor()
        try:
            tutor_profile = TutorProfile.objects.get(user=tutor_user, institution=institution)
            tutor_info = {
                'name': tutor_profile.full_name,
                'email': tutor_profile.email,
                'specialization': tutor_profile.specialization,
                'office': tutor_profile.office,
            }
        except TutorProfile.DoesNotExist:
            tutor_info = {
                'name': tutor_user.get_full_name() or tutor_user.username,
                'email': tutor_user.email,
            }
    
    # Compañeros de grupo
    classmates = []
    if student.group:
        classmates = Student.objects.filter(
            group=student.group,
            is_active=True
        ).exclude(id=student.id).select_related('user')[:10]
    
    context = {
        'institution': institution,
        'user_role': 'student',
        'student': student,
        'tutor_info': tutor_info,
        'classmates': classmates,
    }
    
    return render(request, 'editor/student/my_context.html', context)


# Importar models para Q lookup
from django.db import models
