"""
MÓDULO 6: Django Admin Robusto para Operaciones Globales

Todas las operaciones de administración se realizan EXCLUSIVAMENTE desde /admin/
NO se crean templates ni rutas tipo /admin-panel/

Funcionalidades:
- list_display, search_fields, list_filter avanzados
- Acciones masivas: desactivar usuarios, cambiar estados, exportar CSV
- Auditoría: created_at/updated_at/created_by en modelos clave
- Filtros personalizados
- Exportación CSV
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import format_html, mark_safe
from django.db.models import Count, Q
import csv

from .models import (
    Institution, Membership, Course, Enrollment, TeachingAssignment, 
    TutorProfile, StudentGroup, Student, Project,
    Activity, Submission, Rubric, Feedback,
    IDEProject, ProjectSnapshot, ActivityWorkspace,
    AgentInstance,
    AuditLog, ErrorEvent
)


# ============================================
# HELPERS Y MIXINS
# ============================================

class ExportCSVMixin:
    """Mixin para agregar exportación CSV a cualquier ModelAdmin"""
    
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta.verbose_name_plural}.csv'
        writer = csv.writer(response)
        
        writer.writerow(field_names)
        for obj in queryset:
            row = []
            for field in field_names:
                value = getattr(obj, field)
                if callable(value):
                    value = value()
                row.append(str(value) if value else '')
            writer.writerow(row)
        
        return response
    export_as_csv.short_description = "📥 Exportar seleccionados a CSV"


class AuditMixin:
    """Mixin para guardar automáticamente created_by"""
    
    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, 'created_by'):
            if not obj.created_by:
                obj.created_by = request.user
        obj.save()


# ============================================
# FILTROS PERSONALIZADOS
# ============================================

class IsActiveListFilter(admin.SimpleListFilter):
    title = 'Estado de Usuario'
    parameter_name = 'user_active'
    
    def lookups(self, request, model_admin):
        return (
            ('active', 'Usuarios Activos'),
            ('inactive', 'Usuarios Inactivos'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(user__is_active=True)
        if self.value() == 'inactive':
            return queryset.filter(user__is_active=False)


class HasSubmissionsFilter(admin.SimpleListFilter):
    title = 'Entregas'
    parameter_name = 'has_submissions'
    
    def lookups(self, request, model_admin):
        return (
            ('yes', 'Con entregas'),
            ('no', 'Sin entregas'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.annotate(sub_count=Count('submissions')).filter(sub_count__gt=0)
        if self.value() == 'no':
            return queryset.annotate(sub_count=Count('submissions')).filter(sub_count=0)


class DeadlineStatusFilter(admin.SimpleListFilter):
    title = 'Estado de Fecha Límite'
    parameter_name = 'deadline_status'
    
    def lookups(self, request, model_admin):
        return (
            ('upcoming', 'Próximas (7 días)'),
            ('passed', 'Vencidas'),
            ('no_deadline', 'Sin fecha límite'),
        )
    
    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'upcoming':
            return queryset.filter(deadline__gte=now, deadline__lte=now + timezone.timedelta(days=7))
        if self.value() == 'passed':
            return queryset.filter(deadline__lt=now)
        if self.value() == 'no_deadline':
            return queryset.filter(deadline__isnull=True)


# ============================================
# MÓDULO 6: INSTITUTION ADMIN (Mejorado)
# ============================================

@admin.register(Institution)
class InstitutionAdmin(ExportCSVMixin, admin.ModelAdmin):
    """
    Admin de Instituciones - Centro de gestión global
    """
    list_display = [
        'name', 'code', 'city', 'status', 'status_badge', 
        'get_tutors_count', 'get_students_count', 'get_courses_count', 
        'get_groups_count', 'get_activities_count', 'created_at'
    ]
    list_filter = ['status', 'country', 'city', 'created_at', 'is_active']
    search_fields = ['name', 'code', 'slug', 'email', 'city', 'address', 'phone']
    readonly_fields = [
        'created_at', 'updated_at', 
        'get_members_count', 'get_tutors_count', 'get_students_count', 
        'get_courses_count', 'get_groups_count', 'get_activities_count',
        'agent_token'
    ]
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    list_per_page = 25
    date_hierarchy = 'created_at'
    list_editable = ['status']
    
    fieldsets = (
        ('Información General', {
            'fields': ('name', 'slug', 'code', 'description', 'logo')
        }),
        ('Información de Contacto', {
            'fields': ('email', 'phone', 'website'),
        }),
        ('Dirección', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('status', 'is_active')
        }),
        ('Agent Token', {
            'fields': ('agent_token',),
            'classes': ('collapse',),
        }),
        ('Estadísticas', {
            'fields': (
                'get_members_count', 'get_tutors_count', 'get_students_count', 
                'get_courses_count', 'get_groups_count', 'get_activities_count'
            ),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'active': '#2ea043',
            'inactive': '#8b949e',
            'pending': '#e3b341',
            'suspended': '#f85149'
        }
        color = colors.get(obj.status, '#8b949e')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:4px; font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'status'
    
    def get_members_count(self, obj):
        return obj.get_members_count()
    get_members_count.short_description = 'Total Miembros'
    
    def get_tutors_count(self, obj):
        return obj.get_tutors_count()
    get_tutors_count.short_description = 'Tutores'
    
    def get_students_count(self, obj):
        return obj.get_students_count()
    get_students_count.short_description = 'Estudiantes'
    
    def get_courses_count(self, obj):
        return obj.get_courses_count()
    get_courses_count.short_description = 'Cursos'
    
    def get_groups_count(self, obj):
        return obj.student_groups.count()
    get_groups_count.short_description = 'Grupos'
    
    def get_activities_count(self, obj):
        return Activity.objects.filter(
            Q(group__institution=obj) | Q(course__institution=obj)
        ).count()
    get_activities_count.short_description = 'Actividades'
    
    actions = ['activate_institutions', 'deactivate_institutions', 'suspend_institutions', 'export_as_csv']
    
    @admin.action(description='✅ Activar instituciones seleccionadas')
    def activate_institutions(self, request, queryset):
        updated = queryset.update(status='active', is_active=True)
        self.message_user(request, f'{updated} institución(es) activada(s).')
    
    @admin.action(description='⏸️ Desactivar instituciones seleccionadas')
    def deactivate_institutions(self, request, queryset):
        updated = queryset.update(status='inactive', is_active=False)
        self.message_user(request, f'{updated} institución(es) desactivada(s).')
    
    @admin.action(description='🚫 Suspender instituciones seleccionadas')
    def suspend_institutions(self, request, queryset):
        updated = queryset.update(status='suspended', is_active=False)
        self.message_user(request, f'{updated} institución(es) suspendida(s).')


# ============================================
# MEMBERSHIP ADMIN (Mejorado)
# ============================================

@admin.register(Membership)
class MembershipAdmin(ExportCSVMixin, admin.ModelAdmin):
    list_display = ['user', 'get_user_email', 'institution', 'role_badge', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'institution', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'institution__name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user', 'institution']
    list_editable = ['is_active']
    ordering = ['institution', 'role', 'user__username']
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'
    get_user_email.admin_order_field = 'user__email'
    
    def role_badge(self, obj):
        colors = {
            'admin': '#f85149',
            'institution': '#a371f7',
            'tutor': '#58a6ff',
            'student': '#2ea043'
        }
        color = colors.get(obj.role, '#8b949e')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 6px; border-radius:3px; font-size:11px;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = 'Rol'
    role_badge.admin_order_field = 'role'
    
    actions = ['activate_memberships', 'deactivate_memberships', 'export_as_csv']
    
    @admin.action(description='✅ Activar membresías')
    def activate_memberships(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} membresía(s) activada(s).')
    
    @admin.action(description='⏸️ Desactivar membresías')
    def deactivate_memberships(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} membresía(s) desactivada(s).')


# ============================================
# COURSE ADMIN (Mejorado)
# ============================================

@admin.register(Course)
class CourseAdmin(ExportCSVMixin, AuditMixin, admin.ModelAdmin):
    list_display = [
        'name', 'code', 'institution', 'grade_level', 'status', 'status_badge', 
        'academic_year', 'get_students_count', 'get_activities_count', 'is_active'
    ]
    list_filter = ['institution', 'status', 'grade_level', 'academic_year', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'institution__name', 'tutor__username', 'description']
    readonly_fields = ['created_at', 'updated_at', 'get_students_count', 'get_activities_count']
    raw_id_fields = ['institution', 'tutor']
    list_editable = ['status', 'is_active']
    ordering = ['institution', '-academic_year', 'name']
    
    def status_badge(self, obj):
        colors = {'active': '#2ea043', 'inactive': '#8b949e', 'archived': '#6e7681'}
        color = colors.get(obj.status, '#8b949e')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 6px; border-radius:3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def get_students_count(self, obj):
        return obj.get_students_count()
    get_students_count.short_description = 'Estudiantes'
    
    def get_activities_count(self, obj):
        return obj.activities.count()
    get_activities_count.short_description = 'Actividades'
    
    actions = ['activate_courses', 'deactivate_courses', 'archive_courses', 'export_as_csv']
    
    @admin.action(description='✅ Activar cursos')
    def activate_courses(self, request, queryset):
        queryset.update(status='active', is_active=True)
        self.message_user(request, f'{queryset.count()} curso(s) activado(s).')
    
    @admin.action(description='⏸️ Desactivar cursos')
    def deactivate_courses(self, request, queryset):
        queryset.update(status='inactive', is_active=False)
        self.message_user(request, f'{queryset.count()} curso(s) desactivado(s).')
    
    @admin.action(description='📦 Archivar cursos')
    def archive_courses(self, request, queryset):
        queryset.update(status='archived', is_active=False)
        self.message_user(request, f'{queryset.count()} curso(s) archivado(s).')


# ============================================
# ENROLLMENT ADMIN (Mejorado)
# ============================================

@admin.register(Enrollment)
class EnrollmentAdmin(ExportCSVMixin, admin.ModelAdmin):
    list_display = ['student', 'get_student_email', 'course', 'status_badge', 'enrolled_at', 'get_institution']
    list_filter = ['status', 'enrolled_at', 'course__institution', 'course']
    search_fields = ['student__username', 'student__email', 'student__first_name', 'student__last_name', 'course__name']
    readonly_fields = ['enrolled_at', 'updated_at']
    raw_id_fields = ['student', 'course']
    date_hierarchy = 'enrolled_at'
    
    def get_student_email(self, obj):
        return obj.student.email
    get_student_email.short_description = 'Email'
    
    def status_badge(self, obj):
        colors = {'active': '#2ea043', 'inactive': '#8b949e', 'completed': '#58a6ff', 'dropped': '#f85149'}
        color = colors.get(obj.status, '#8b949e')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 6px; border-radius:3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def get_institution(self, obj):
        return obj.institution.name if obj.institution else "-"
    get_institution.short_description = 'Institución'
    
    actions = ['activate_enrollments', 'complete_enrollments', 'drop_enrollments', 'export_as_csv']
    
    @admin.action(description='✅ Activar matrículas')
    def activate_enrollments(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f'{queryset.count()} matrícula(s) activada(s).')
    
    @admin.action(description='🎓 Marcar como completadas')
    def complete_enrollments(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f'{queryset.count()} matrícula(s) completada(s).')
    
    @admin.action(description='🚫 Dar de baja')
    def drop_enrollments(self, request, queryset):
        queryset.update(status='dropped')
        self.message_user(request, f'{queryset.count()} matrícula(s) dada(s) de baja.')


# ============================================
# TEACHING ASSIGNMENT ADMIN
# ============================================

@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(ExportCSVMixin, admin.ModelAdmin):
    list_display = ['tutor', 'get_tutor_email', 'course', 'status_badge', 'assigned_at', 'get_institution']
    list_filter = ['status', 'assigned_at', 'course__institution']
    search_fields = ['tutor__username', 'tutor__email', 'course__name', 'course__code']
    readonly_fields = ['assigned_at', 'updated_at']
    raw_id_fields = ['tutor', 'course']
    
    def get_tutor_email(self, obj):
        return obj.tutor.email
    get_tutor_email.short_description = 'Email'
    
    def status_badge(self, obj):
        colors = {'active': '#2ea043', 'inactive': '#8b949e'}
        color = colors.get(obj.status, '#8b949e')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 6px; border-radius:3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def get_institution(self, obj):
        return obj.institution.name if obj.institution else "-"
    get_institution.short_description = 'Institución'


# ============================================
# TUTOR PROFILE ADMIN (Mejorado)
# ============================================

class TutorProfileCreationForm(forms.ModelForm):
    """Formulario para crear TutorProfile con creación automática de User y Membership"""
    username = forms.CharField(max_length=150, help_text="Nombre de usuario para login")
    email = forms.EmailField(help_text="Email del tutor")
    password = forms.CharField(widget=forms.PasswordInput, help_text="Contraseña inicial")
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    
    class Meta:
        model = TutorProfile
        fields = ['institution', 'employee_id', 'title', 'specialization', 'bio', 'phone', 'office', 'status']
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ya existe un usuario con este nombre de usuario.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un usuario con este email.")
        return email


@admin.register(TutorProfile)
class TutorProfileAdmin(ExportCSVMixin, admin.ModelAdmin):
    """
    CRUD de Tutores EXCLUSIVAMENTE desde aquí
    """
    list_display = [
        'get_full_name', 'user', 'get_email', 'institution', 'status_badge',
        'get_groups_count', 'get_students_count', 'get_activities_count', 'created_at'
    ]
    list_filter = ['status', 'institution', IsActiveListFilter, 'created_at']
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'employee_id', 'institution__name', 'specialization'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 
        'get_groups_count', 'get_students_count', 'get_activities_count', 'get_email'
    ]
    raw_id_fields = ['user', 'institution']
    ordering = ['institution', 'user__last_name']
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'get_email'),
        }),
        ('Institución', {
            'fields': ('institution',),
        }),
        ('Información Profesional', {
            'fields': ('employee_id', 'title', 'specialization', 'bio')
        }),
        ('Contacto', {
            'fields': ('phone', 'office')
        }),
        ('Estado', {
            'fields': ('status',),
        }),
        ('Estadísticas', {
            'fields': ('get_groups_count', 'get_students_count', 'get_activities_count'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Crear Usuario', {
            'fields': ('username', 'email', 'password', 'first_name', 'last_name'),
        }),
        ('Institución', {
            'fields': ('institution',),
        }),
        ('Información Profesional', {
            'fields': ('employee_id', 'title', 'specialization', 'bio')
        }),
        ('Contacto', {
            'fields': ('phone', 'office')
        }),
        ('Estado', {
            'fields': ('status',),
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)
    
    def get_form(self, request, obj=None, **kwargs):
        if not obj:
            kwargs['form'] = TutorProfileCreationForm
        return super().get_form(request, obj, **kwargs)
    
    def get_full_name(self, obj):
        return obj.full_name
    get_full_name.short_description = 'Nombre'
    get_full_name.admin_order_field = 'user__last_name'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def status_badge(self, obj):
        colors = {'active': '#2ea043', 'inactive': '#8b949e', 'on_leave': '#e3b341', 'suspended': '#f85149'}
        color = colors.get(obj.status, '#8b949e')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 6px; border-radius:3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def get_groups_count(self, obj):
        return StudentGroup.objects.filter(tutor=obj.user).count()
    get_groups_count.short_description = 'Grupos'
    
    def get_students_count(self, obj):
        return obj.get_students_count()
    get_students_count.short_description = 'Estudiantes'
    
    def get_activities_count(self, obj):
        return Activity.objects.filter(
            Q(group__tutor=obj.user) | Q(created_by=obj.user)
        ).count()
    get_activities_count.short_description = 'Actividades'
    
    def save_model(self, request, obj, form, change):
        if not change:
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', ''),
            )
            obj.user = user
            obj.created_by = request.user
            obj.save()
            
            Membership.objects.get_or_create(
                user=user,
                institution=obj.institution,
                defaults={'role': 'tutor', 'is_active': obj.status == 'active'}
            )
        else:
            obj.save()
            Membership.objects.filter(
                user=obj.user, institution=obj.institution, role='tutor'
            ).update(is_active=obj.status == 'active')
    
    actions = ['activate_tutors', 'deactivate_tutors', 'suspend_tutors', 'disable_user_accounts', 'export_as_csv']
    
    @admin.action(description='✅ Activar tutores')
    def activate_tutors(self, request, queryset):
        for tutor in queryset:
            tutor.activate()
        self.message_user(request, f'{queryset.count()} tutor(es) activado(s).')
    
    @admin.action(description='⏸️ Desactivar tutores')
    def deactivate_tutors(self, request, queryset):
        for tutor in queryset:
            tutor.deactivate()
        self.message_user(request, f'{queryset.count()} tutor(es) desactivado(s).')
    
    @admin.action(description='🚫 Suspender tutores')
    def suspend_tutors(self, request, queryset):
        queryset.update(status='suspended')
        for tutor in queryset:
            Membership.objects.filter(user=tutor.user, institution=tutor.institution, role='tutor').update(is_active=False)
        self.message_user(request, f'{queryset.count()} tutor(es) suspendido(s).')
    
    @admin.action(description='🔒 Deshabilitar cuentas de usuario')
    def disable_user_accounts(self, request, queryset):
        count = 0
        for tutor in queryset:
            tutor.user.is_active = False
            tutor.user.save()
            count += 1
        self.message_user(request, f'{count} cuenta(s) de usuario deshabilitada(s).')


# ============================================
# STUDENT GROUP ADMIN (Mejorado)
# ============================================

@admin.register(StudentGroup)
class StudentGroupAdmin(ExportCSVMixin, AuditMixin, admin.ModelAdmin):
    """
    Admin de Grupos - Supervisión global
    """
    list_display = [
        'name', 'code', 'institution', 'tutor', 'academic_year', 
        'status_badge', 'get_students_count', 'max_students', 'get_activities_count'
    ]
    list_filter = ['status', 'institution', 'academic_year', 'semester', 'tutor', 'created_at']
    search_fields = ['name', 'code', 'institution__name', 'tutor__username', 'tutor__first_name', 'tutor__last_name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'get_students_count', 'get_available_slots', 'get_activities_count']
    raw_id_fields = ['institution', 'tutor', 'created_by']
    ordering = ['institution', '-academic_year', 'name']
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Institución y Tutor', {
            'fields': ('institution', 'tutor'),
        }),
        ('Información del Grupo', {
            'fields': ('name', 'code', 'description')
        }),
        ('Período Académico', {
            'fields': ('academic_year', 'semester')
        }),
        ('Configuración', {
            'fields': ('status', 'max_students')
        }),
        ('Estadísticas', {
            'fields': ('get_students_count', 'get_available_slots', 'get_activities_count'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {'active': '#2ea043', 'inactive': '#8b949e', 'archived': '#6e7681'}
        color = colors.get(obj.status, '#8b949e')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 6px; border-radius:3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def get_students_count(self, obj):
        return obj.get_students_count()
    get_students_count.short_description = 'Estudiantes'
    
    def get_available_slots(self, obj):
        return obj.get_available_slots()
    get_available_slots.short_description = 'Espacios Disp.'
    
    def get_activities_count(self, obj):
        return obj.activities.count()
    get_activities_count.short_description = 'Actividades'
    
    actions = ['activate_groups', 'deactivate_groups', 'archive_groups', 'export_as_csv']
    
    @admin.action(description='✅ Activar grupos')
    def activate_groups(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f'{queryset.count()} grupo(s) activado(s).')
    
    @admin.action(description='⏸️ Desactivar grupos')
    def deactivate_groups(self, request, queryset):
        queryset.update(status='inactive')
        self.message_user(request, f'{queryset.count()} grupo(s) desactivado(s).')
    
    @admin.action(description='📦 Archivar grupos')
    def archive_groups(self, request, queryset):
        queryset.update(status='archived')
        self.message_user(request, f'{queryset.count()} grupo(s) archivado(s).')


# ============================================
# STUDENT ADMIN (Mejorado)
# ============================================

@admin.register(Student)
class StudentAdmin(ExportCSVMixin, AuditMixin, admin.ModelAdmin):
    """
    Admin de Estudiantes - Supervisión global
    """
    list_display = [
        'student_id', 'get_full_name', 'get_email', 'institution', 'group', 
        'tutor', 'is_active_badge', 'get_submissions_count', 'get_projects_count'
    ]
    list_filter = ['is_active', 'institution', 'group', 'tutor', IsActiveListFilter, 'created_at']
    search_fields = [
        'student_id', 'user__username', 'user__email',
        'user__first_name', 'user__last_name',
        'institution__name', 'group__name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'get_projects_count', 'get_submissions_count']
    raw_id_fields = ['user', 'institution', 'group', 'tutor', 'course', 'created_by']
    ordering = ['institution', 'group', 'student_id']
    list_per_page = 25
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'student_id'),
        }),
        ('Asignaciones', {
            'fields': ('institution', 'group', 'tutor', 'course'),
        }),
        ('Información de Contacto', {
            'fields': ('phone', 'emergency_contact', 'emergency_phone')
        }),
        ('Estado y Notas', {
            'fields': ('is_active', 'notes')
        }),
        ('Estadísticas', {
            'fields': ('get_projects_count', 'get_submissions_count'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.full_name
    get_full_name.short_description = 'Nombre'
    get_full_name.admin_order_field = 'user__last_name'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def is_active_badge(self, obj):
        if obj.is_active and obj.user.is_active:
            return mark_safe('<span style="color:#2ea043;">✓ Activo</span>')
        return mark_safe('<span style="color:#f85149;">✗ Inactivo</span>')
    is_active_badge.short_description = 'Estado'
    
    def get_projects_count(self, obj):
        return obj.get_projects_count()
    get_projects_count.short_description = 'Proyectos'
    
    def get_submissions_count(self, obj):
        return Submission.objects.filter(student=obj.user).count()
    get_submissions_count.short_description = 'Entregas'
    
    actions = ['activate_students', 'deactivate_students', 'disable_user_accounts', 'export_as_csv']
    
    @admin.action(description='✅ Activar estudiantes')
    def activate_students(self, request, queryset):
        queryset.update(is_active=True)
        for student in queryset:
            student.user.is_active = True
            student.user.save()
        self.message_user(request, f'{queryset.count()} estudiante(s) activado(s).')
    
    @admin.action(description='⏸️ Desactivar estudiantes')
    def deactivate_students(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} estudiante(s) desactivado(s).')
    
    @admin.action(description='🔒 Deshabilitar cuentas de usuario')
    def disable_user_accounts(self, request, queryset):
        count = 0
        for student in queryset:
            student.user.is_active = False
            student.user.save()
            count += 1
        self.message_user(request, f'{count} cuenta(s) de usuario deshabilitada(s).')


# ============================================
# PROJECT ADMIN
# ============================================

@admin.register(Project)
class ProjectAdmin(ExportCSVMixin, admin.ModelAdmin):
    list_display = ['name', 'student', 'get_group', 'get_institution', 'created_at', 'updated_at', 'is_active']
    list_filter = ['is_active', 'student__institution', 'student__group', 'created_at']
    search_fields = ['name', 'student__user__username', 'student__student_id', 'description']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['student']
    date_hierarchy = 'created_at'
    
    def get_group(self, obj):
        return obj.student.group.name if obj.student.group else "-"
    get_group.short_description = 'Grupo'
    
    def get_institution(self, obj):
        return obj.student.institution.name if obj.student.institution else "-"
    get_institution.short_description = 'Institución'
    
    actions = ['activate_projects', 'deactivate_projects', 'export_as_csv']
    
    @admin.action(description='✅ Activar proyectos')
    def activate_projects(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} proyecto(s) activado(s).')
    
    @admin.action(description='⏸️ Desactivar proyectos')
    def deactivate_projects(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} proyecto(s) desactivado(s).')


# ============================================
# USER ADMIN (Mejorado)
# ============================================

class TutorProfileInline(admin.StackedInline):
    model = TutorProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Tutor'
    fk_name = 'user'
    extra = 0
    readonly_fields = ['created_at', 'updated_at', 'created_by']


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    raw_id_fields = ['institution']


class StudentInline(admin.StackedInline):
    model = Student
    can_delete = False
    verbose_name_plural = 'Perfil de Estudiante'
    fk_name = 'user'
    extra = 0


class CustomUserAdmin(BaseUserAdmin):
    inlines = (MembershipInline, TutorProfileInline, StudentInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active_badge', 'is_staff', 'get_roles', 'last_login')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'last_login')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-last_login', 'username')
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return mark_safe('<span style="color:#2ea043;">✓</span>')
        return mark_safe('<span style="color:#f85149;">✗</span>')
    is_active_badge.short_description = 'Activo'
    
    def get_roles(self, obj):
        memberships = Membership.objects.filter(user=obj, is_active=True)
        if not memberships.exists():
            if obj.is_superuser:
                return mark_safe('<span style="color:#f85149;">🔴 Superuser</span>')
            return "Sin rol"
        roles = []
        for m in memberships[:2]:
            colors = {'admin': '#f85149', 'institution': '#a371f7', 'tutor': '#58a6ff', 'student': '#2ea043'}
            color = colors.get(m.role, '#8b949e')
            roles.append(f'<span style="color:{color};">{m.get_role_display()}</span>')
        if memberships.count() > 2:
            roles.append(f'<span style="color:#8b949e;">+{memberships.count() - 2}</span>')
        return mark_safe(", ".join(roles))
    get_roles.short_description = 'Roles'
    
    actions = ['activate_users', 'deactivate_users']
    
    @admin.action(description='✅ Activar usuarios')
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} usuario(s) activado(s).')
    
    @admin.action(description='🔒 Desactivar usuarios')
    def deactivate_users(self, request, queryset):
        # Excluir superusers de la desactivación
        non_super = queryset.filter(is_superuser=False)
        non_super.update(is_active=False)
        self.message_user(request, f'{non_super.count()} usuario(s) desactivado(s). Superusers excluidos.')


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ============================================
# ACTIVITY ADMIN (Mejorado)
# ============================================

@admin.register(Activity)
class ActivityAdmin(ExportCSVMixin, AuditMixin, admin.ModelAdmin):
    """
    Admin de Actividades - Supervisión global
    """
    list_display = [
        'title', 'get_target', 'get_tutor', 'status_badge', 'deadline_badge', 
        'max_score', 'get_submissions_count', 'get_pending_count', 'created_at'
    ]
    list_filter = [
        'status', 'allow_resubmit', 'allow_late_submit', DeadlineStatusFilter, HasSubmissionsFilter,
        'group__institution', 'course__institution', 'created_at'
    ]
    search_fields = ['title', 'objective', 'instructions', 'group__name', 'course__name', 'created_by__username']
    readonly_fields = [
        'created_at', 'updated_at', 'published_at', 
        'get_submissions_count', 'get_pending_submissions_count', 'get_target_students_count'
    ]
    raw_id_fields = ['course', 'group', 'created_by']
    date_hierarchy = 'deadline'
    ordering = ['-created_at']
    list_per_page = 25
    
    fieldsets = (
        ('Asignación', {
            'fields': ('group', 'course', 'created_by'),
        }),
        ('Información General', {
            'fields': ('title', 'objective', 'instructions')
        }),
        ('Configuración', {
            'fields': ('deadline', 'max_score', 'status', 'allow_resubmit', 'allow_late_submit')
        }),
        ('Estadísticas', {
            'fields': ('get_target_students_count', 'get_submissions_count', 'get_pending_submissions_count'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_target(self, obj):
        if obj.group:
            return format_html('<span style="color:#58a6ff;">📁 {}</span>', obj.group.name)
        if obj.course:
            return format_html('<span style="color:#a371f7;">📚 {}</span>', obj.course.name)
        return "-"
    get_target.short_description = 'Destino'
    
    def get_tutor(self, obj):
        tutor = obj.tutor
        if tutor:
            return tutor.get_full_name() or tutor.username
        return "-"
    get_tutor.short_description = 'Tutor'
    
    def status_badge(self, obj):
        colors = {'draft': '#e3b341', 'published': '#2ea043', 'closed': '#8b949e'}
        icons = {'draft': '📝', 'published': '✅', 'closed': '🔒'}
        color = colors.get(obj.status, '#8b949e')
        icon = icons.get(obj.status, '')
        return format_html(
            '<span style="color:{};">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def deadline_badge(self, obj):
        if not obj.deadline:
            return mark_safe('<span style="color:#8b949e;">Sin fecha</span>')
        now = timezone.now()
        if obj.deadline < now:
            return mark_safe('<span style="color:#f85149;">⏰ Vencida</span>')
        days_left = (obj.deadline - now).days
        if days_left <= 3:
            return format_html('<span style="color:#e3b341;">⚠️ {} días</span>', days_left)
        return format_html('<span style="color:#2ea043;">{}</span>', obj.deadline.strftime('%d/%m/%Y'))
    deadline_badge.short_description = 'Fecha Límite'
    
    def get_submissions_count(self, obj):
        return obj.get_submissions_count()
    get_submissions_count.short_description = 'Entregas'
    
    def get_pending_count(self, obj):
        count = obj.get_pending_submissions_count()
        if count > 0:
            return format_html('<span style="color:#e3b341;">{}</span>', count)
        return count
    get_pending_count.short_description = 'Pendientes'
    
    def get_pending_submissions_count(self, obj):
        return obj.get_pending_submissions_count()
    get_pending_submissions_count.short_description = 'Pend. Calif.'
    
    def get_target_students_count(self, obj):
        return obj.get_target_students_count()
    get_target_students_count.short_description = 'Estudiantes'
    
    actions = ['publish_activities', 'close_activities', 'draft_activities', 'export_as_csv']
    
    @admin.action(description='✅ Publicar actividades')
    def publish_activities(self, request, queryset):
        count = queryset.filter(status='draft').update(status='published', published_at=timezone.now())
        self.message_user(request, f'{count} actividad(es) publicada(s).')
    
    @admin.action(description='🔒 Cerrar actividades')
    def close_activities(self, request, queryset):
        queryset.update(status='closed')
        self.message_user(request, f'{queryset.count()} actividad(es) cerrada(s).')
    
    @admin.action(description='📝 Pasar a borrador')
    def draft_activities(self, request, queryset):
        queryset.update(status='draft', published_at=None)
        self.message_user(request, f'{queryset.count()} actividad(es) pasada(s) a borrador.')


# ============================================
# SUBMISSION ADMIN (Mejorado)
# ============================================

@admin.register(Submission)
class SubmissionAdmin(ExportCSVMixin, admin.ModelAdmin):
    """
    Admin de Entregas - Supervisión global
    """
    list_display = [
        'get_student_name', 'activity', 'attempt', 'status_badge', 
        'score_display', 'is_late_badge', 'submitted_at', 'graded_at', 'get_institution'
    ]
    list_filter = [
        'status', 'is_late', 'submitted_at', 'graded_at',
        'activity__group__institution', 'activity__course__institution'
    ]
    search_fields = [
        'student__username', 'student__email', 'student__first_name', 'student__last_name',
        'activity__title', 'activity__group__name'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'submitted_at', 'graded_at', 'is_late', 'is_read_only'
    ]
    raw_id_fields = ['activity', 'student', 'graded_by']
    date_hierarchy = 'submitted_at'
    ordering = ['-submitted_at', '-created_at']
    list_per_page = 25
    
    fieldsets = (
        ('Información', {
            'fields': ('activity', 'student', 'attempt')
        }),
        ('Estado', {
            'fields': ('status', 'is_late', 'is_read_only')
        }),
        ('Contenido', {
            'fields': ('xml_content', 'arduino_code', 'notes'),
            'classes': ('collapse',)
        }),
        ('Calificación', {
            'fields': ('score', 'graded_by', 'graded_at')
        }),
        ('Fechas', {
            'fields': ('submitted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_student_name(self, obj):
        return obj.student_name
    get_student_name.short_description = 'Estudiante'
    get_student_name.admin_order_field = 'student__last_name'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#8b949e', 'in_progress': '#e3b341', 
            'submitted': '#58a6ff', 'graded': '#2ea043', 'returned': '#a371f7'
        }
        icons = {
            'pending': '⏳', 'in_progress': '✏️',
            'submitted': '📨', 'graded': '✅', 'returned': '↩️'
        }
        color = colors.get(obj.status, '#8b949e')
        icon = icons.get(obj.status, '')
        return format_html(
            '<span style="color:{};">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def score_display(self, obj):
        if obj.score is not None:
            max_score = obj.activity.max_score
            percentage = (obj.score / max_score * 100) if max_score else 0
            color = '#2ea043' if percentage >= 60 else '#e3b341' if percentage >= 40 else '#f85149'
            return format_html('<span style="color:{};">{}/{} ({:.0f}%)</span>', color, obj.score, max_score, percentage)
        return "-"
    score_display.short_description = 'Calificación'
    
    def is_late_badge(self, obj):
        if obj.is_late:
            return mark_safe('<span style="color:#e3b341;">⚠️ Tardía</span>')
        return mark_safe('<span style="color:#2ea043;">✓</span>')
    is_late_badge.short_description = 'A Tiempo'
    
    def get_institution(self, obj):
        return obj.institution.name if obj.institution else "-"
    get_institution.short_description = 'Institución'
    
    actions = ['mark_as_graded', 'mark_as_submitted', 'mark_as_reviewed', 'reset_to_in_progress', 'export_as_csv']
    
    @admin.action(description='✅ Marcar como calificadas')
    def mark_as_graded(self, request, queryset):
        queryset.update(status='graded', graded_at=timezone.now(), graded_by=request.user)
        self.message_user(request, f'{queryset.count()} entrega(s) marcada(s) como calificada(s).')
    
    @admin.action(description='📨 Marcar como entregadas')
    def mark_as_submitted(self, request, queryset):
        queryset.update(status='submitted')
        self.message_user(request, f'{queryset.count()} entrega(s) marcada(s) como entregada(s).')
    
    @admin.action(description='👁️ Marcar como revisadas')
    def mark_as_reviewed(self, request, queryset):
        # Estado "reviewed" no existe, usar "graded" sin score
        queryset.update(status='graded', graded_at=timezone.now(), graded_by=request.user)
        self.message_user(request, f'{queryset.count()} entrega(s) marcada(s) como revisada(s).')
    
    @admin.action(description='🔄 Resetear a en progreso')
    def reset_to_in_progress(self, request, queryset):
        queryset.update(status='in_progress', is_read_only=False, score=None, graded_at=None, graded_by=None)
        self.message_user(request, f'{queryset.count()} entrega(s) reseteada(s).')


# ============================================
# RUBRIC & FEEDBACK ADMIN
# ============================================

@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    list_display = ['activity', 'get_total_max_score', 'created_at']
    list_filter = ['created_at', 'activity__group__institution', 'activity__course__institution']
    search_fields = ['activity__title', 'activity__group__name', 'activity__course__name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['activity']


@admin.register(Feedback)
class FeedbackAdmin(ExportCSVMixin, admin.ModelAdmin):
    list_display = ['submission', 'tutor', 'score', 'get_percentage_score', 'created_at', 'get_institution']
    list_filter = ['created_at', 'submission__activity__group__institution', 'submission__activity__course__institution']
    search_fields = ['submission__student__username', 'submission__activity__title', 'tutor__username', 'comments']
    readonly_fields = ['created_at', 'updated_at', 'get_percentage_score']
    raw_id_fields = ['submission', 'tutor']
    date_hierarchy = 'created_at'
    
    def get_percentage_score(self, obj):
        return f"{obj.get_percentage_score():.1f}%" if obj.get_percentage_score() else "-"
    get_percentage_score.short_description = 'Porcentaje'
    
    def get_institution(self, obj):
        return obj.institution.name if obj.institution else "-"
    get_institution.short_description = 'Institución'


# ============================================
# IDE PROJECT & WORKSPACE ADMIN
# ============================================

@admin.register(IDEProject)
class IDEProjectAdmin(ExportCSVMixin, admin.ModelAdmin):
    list_display = ['name', 'owner', 'institution', 'updated_at', 'is_frozen_badge']
    list_filter = ['created_at', 'updated_at', 'institution']
    search_fields = ['name', 'owner__username', 'owner__email', 'institution__name']
    readonly_fields = ['created_at', 'updated_at', 'get_last_modified']
    raw_id_fields = ['owner', 'institution']
    date_hierarchy = 'updated_at'
    
    def is_frozen_badge(self, obj):
        if obj.is_frozen():
            return mark_safe('<span style="color:#58a6ff;">🧊 Congelado</span>')
        return mark_safe('<span style="color:#2ea043;">✓ Editable</span>')
    is_frozen_badge.short_description = 'Estado'


@admin.register(ProjectSnapshot)
class ProjectSnapshotAdmin(admin.ModelAdmin):
    list_display = ['project', 'label', 'created_at', 'get_institution']
    list_filter = ['created_at', 'project__institution']
    search_fields = ['project__name', 'label', 'project__owner__username']
    readonly_fields = ['created_at']
    raw_id_fields = ['project']
    date_hierarchy = 'created_at'
    
    def get_institution(self, obj):
        return obj.institution.name if obj.institution else "-"
    get_institution.short_description = 'Institución'


@admin.register(ActivityWorkspace)
class ActivityWorkspaceAdmin(admin.ModelAdmin):
    list_display = ['activity', 'student', 'project', 'status_badge', 'frozen_at', 'get_institution']
    list_filter = ['status', 'frozen_at', 'created_at', 'activity__group__institution', 'activity__course__institution']
    search_fields = ['activity__title', 'student__username', 'student__email', 'project__name']
    readonly_fields = ['created_at', 'updated_at', 'frozen_at']
    raw_id_fields = ['activity', 'student', 'project']
    date_hierarchy = 'created_at'
    
    def status_badge(self, obj):
        colors = {'in_progress': '#e3b341', 'frozen': '#58a6ff'}
        color = colors.get(obj.status, '#8b949e')
        return format_html(
            '<span style="color:{};">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def get_institution(self, obj):
        return obj.institution.name if obj.institution else "-"
    get_institution.short_description = 'Institución'


# ============================================
# AGENT INSTANCE ADMIN
# ============================================

@admin.register(AgentInstance)
class AgentInstanceAdmin(ExportCSVMixin, admin.ModelAdmin):
    list_display = ['hostname', 'institution', 'os', 'agent_version', 'status_badge', 'last_seen', 'is_online_display']
    list_filter = ['status', 'os', 'agent_version', 'created_at', 'last_seen', 'institution']
    search_fields = ['hostname', 'institution__name', 'os', 'agent_version']
    readonly_fields = ['created_at', 'updated_at', 'last_seen', 'is_online_display']
    raw_id_fields = ['institution']
    date_hierarchy = 'last_seen'
    
    fieldsets = (
        ('Identificación', {
            'fields': ('institution', 'hostname', 'os')
        }),
        ('Versiones', {
            'fields': ('agent_version', 'ide_version_compatible')
        }),
        ('Estado', {
            'fields': ('status', 'last_seen', 'is_online_display')
        }),
        ('Metadata', {
            'fields': ('meta',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {'online': '#2ea043', 'offline': '#8b949e', 'error': '#f85149'}
        color = colors.get(obj.status, '#8b949e')
        return format_html(
            '<span style="color:{};">● {}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def is_online_display(self, obj):
        if obj.is_online():
            return mark_safe('<span style="color:#2ea043;">🟢 Online</span>')
        return mark_safe('<span style="color:#8b949e;">⚪ Offline</span>')
    is_online_display.short_description = 'Conectado'


# ============================================
# AUDIT LOG & ERROR EVENT ADMIN
# ============================================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['actor', 'institution', 'action_badge', 'entity', 'entity_id', 'ts']
    list_filter = ['action', 'entity', 'ts', 'institution']
    search_fields = ['actor__username', 'actor__email', 'entity', 'entity_id', 'institution__name']
    readonly_fields = ['ts', 'actor', 'institution', 'action', 'entity', 'entity_id', 'metadata']
    raw_id_fields = ['actor', 'institution']
    date_hierarchy = 'ts'
    
    def action_badge(self, obj):
        colors = {
            'create': '#2ea043', 'update': '#58a6ff', 
            'delete': '#f85149', 'login': '#a371f7', 'logout': '#8b949e'
        }
        color = colors.get(obj.action, '#8b949e')
        return format_html(
            '<span style="color:{};">{}</span>',
            color, obj.action.upper()
        )
    action_badge.short_description = 'Acción'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ErrorEvent)
class ErrorEventAdmin(ExportCSVMixin, admin.ModelAdmin):
    list_display = ['code', 'severity_badge', 'institution', 'user', 'resolved_badge', 'ts']
    list_filter = ['code', 'severity', 'resolved', 'ts', 'institution']
    search_fields = ['code', 'message', 'user__username', 'institution__name']
    readonly_fields = ['ts', 'resolved_at', 'resolved_by']
    raw_id_fields = ['institution', 'user', 'resolved_by']
    date_hierarchy = 'ts'
    
    fieldsets = (
        ('Información General', {
            'fields': ('institution', 'user', 'code', 'severity', 'message')
        }),
        ('Contexto', {
            'fields': ('context',),
            'classes': ('wide',)
        }),
        ('Resolución', {
            'fields': ('resolved', 'resolved_at', 'resolved_by')
        }),
        ('Fecha', {
            'fields': ('ts',)
        }),
    )
    
    def severity_badge(self, obj):
        colors = {'info': '#58a6ff', 'warning': '#e3b341', 'error': '#f85149', 'critical': '#da3633'}
        color = colors.get(obj.severity, '#8b949e')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 6px; border-radius:3px;">{}</span>',
            color, obj.get_severity_display()
        )
    severity_badge.short_description = 'Severidad'
    
    def resolved_badge(self, obj):
        if obj.resolved:
            return mark_safe('<span style="color:#2ea043;">✓ Resuelto</span>')
        return mark_safe('<span style="color:#f85149;">✗ Pendiente</span>')
    resolved_badge.short_description = 'Resuelto'
    
    actions = ['mark_as_resolved', 'mark_as_unresolved', 'export_as_csv']
    
    @admin.action(description='✅ Marcar como resueltos')
    def mark_as_resolved(self, request, queryset):
        queryset.update(resolved=True, resolved_at=timezone.now(), resolved_by=request.user)
        self.message_user(request, f'{queryset.count()} error(es) marcado(s) como resuelto(s).')
    
    @admin.action(description='🔄 Marcar como pendientes')
    def mark_as_unresolved(self, request, queryset):
        queryset.update(resolved=False, resolved_at=None, resolved_by=None)
        self.message_user(request, f'{queryset.count()} error(es) marcado(s) como pendiente(s).')


# ============================================
# CONFIGURACIÓN DEL ADMIN SITE
# ============================================

admin.site.site_header = "🤖 MAX-IDE Administración"
admin.site.site_title = "MAX-IDE Admin"
admin.site.index_title = "Panel de Administración Global"
