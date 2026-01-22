from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from .models import (
    Institution, Membership, Course, Enrollment, TeachingAssignment, 
    TutorProfile, Student, Project,
    Activity, Submission, Rubric, Feedback,
    IDEProject, ProjectSnapshot, ActivityWorkspace,
    AgentInstance,
    AuditLog, ErrorEvent
)


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    """
    MÓDULO 2: Admin de Institución
    
    Todo el CRUD de instituciones se hace desde aquí.
    NO se crean vistas/templates de admin para instituciones.
    """
    list_display = [
        'name', 'code', 'city', 'status', 
        'get_tutors_count', 'get_students_count', 'get_courses_count', 
        'created_at'
    ]
    list_filter = ['status', 'country', 'city', 'created_at']
    search_fields = ['name', 'code', 'slug', 'email', 'city', 'address']
    readonly_fields = [
        'created_at', 'updated_at', 
        'get_members_count', 'get_tutors_count', 'get_students_count', 'get_courses_count',
        'agent_token'
    ]
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información General', {
            'fields': ('name', 'slug', 'code', 'description', 'logo')
        }),
        ('Información de Contacto', {
            'fields': ('email', 'phone', 'website'),
            'description': 'Datos de contacto de la institución'
        }),
        ('Dirección', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('status', 'is_active')
        }),
        ('Configuración del Agent', {
            'fields': ('agent_token',),
            'classes': ('collapse',),
            'description': 'Token para registro de Agents locales'
        }),
        ('Estadísticas', {
            'fields': ('get_members_count', 'get_tutors_count', 'get_students_count', 'get_courses_count'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
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
    
    actions = ['activate_institutions', 'deactivate_institutions']
    
    @admin.action(description='Activar instituciones seleccionadas')
    def activate_institutions(self, request, queryset):
        updated = queryset.update(status='active', is_active=True)
        self.message_user(request, f'{updated} institución(es) activada(s).')
    
    @admin.action(description='Desactivar instituciones seleccionadas')
    def deactivate_institutions(self, request, queryset):
        updated = queryset.update(status='inactive', is_active=False)
        self.message_user(request, f'{updated} institución(es) desactivada(s).')


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'institution', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'institution', 'created_at']
    search_fields = ['user__username', 'user__email', 'institution__name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user', 'institution']
    fieldsets = (
        ('Membresía', {
            'fields': ('user', 'institution', 'role')
        }),
        ('Estado', {
            'fields': ('is_active', 'notes')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'institution', 'grade_level', 'status', 'academic_year', 'is_active', 'get_students_count']
    list_filter = ['institution', 'status', 'grade_level', 'academic_year', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'institution__name', 'tutor__username']
    readonly_fields = ['created_at', 'updated_at', 'get_students_count']
    raw_id_fields = ['institution', 'tutor']
    fieldsets = (
        ('Información General', {
            'fields': ('institution', 'name', 'code', 'description', 'grade_level')
        }),
        ('Año Académico', {
            'fields': ('academic_year',)
        }),
        ('Estado', {
            'fields': ('status', 'is_active')
        }),
        ('Tutor (Legacy)', {
            'fields': ('tutor',),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': ('get_students_count',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_students_count(self, obj):
        return obj.get_students_count()
    get_students_count.short_description = 'Estudiantes'


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'enrolled_at', 'get_institution']
    list_filter = ['status', 'enrolled_at', 'course__institution']
    search_fields = ['student__username', 'student__email', 'course__name', 'course__code']
    readonly_fields = ['enrolled_at', 'updated_at']
    raw_id_fields = ['student', 'course']
    
    def get_institution(self, obj):
        return obj.institution.name if obj.institution else "-"
    get_institution.short_description = 'Institución'


@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = ['tutor', 'course', 'status', 'assigned_at', 'get_institution']
    list_filter = ['status', 'assigned_at', 'course__institution']
    search_fields = ['tutor__username', 'tutor__email', 'course__name', 'course__code']
    readonly_fields = ['assigned_at', 'updated_at']
    raw_id_fields = ['tutor', 'course']
    
    def get_institution(self, obj):
        return obj.institution.name if obj.institution else "-"
    get_institution.short_description = 'Institución'


# ============================================
# MÓDULO 3: TUTOR PROFILE ADMIN
# ============================================

class TutorProfileCreationForm(forms.ModelForm):
    """Formulario para crear TutorProfile con creación automática de User y Membership"""
    username = forms.CharField(max_length=150, help_text="Nombre de usuario para login")
    email = forms.EmailField(help_text="Email del tutor (también para login)")
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
class TutorProfileAdmin(admin.ModelAdmin):
    """
    MÓDULO 3: Admin de Perfiles de Tutor
    
    Todo el CRUD de tutores se hace EXCLUSIVAMENTE desde aquí.
    NO hay rutas/templates tipo /admin-panel/tutors.
    """
    list_display = [
        'get_full_name', 'user', 'institution', 'title', 'specialization',
        'status', 'get_courses_count', 'get_students_count', 'created_at'
    ]
    list_filter = ['status', 'institution', 'created_at']
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'employee_id', 'institution__name', 'specialization'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 
        'get_courses_count', 'get_students_count', 'get_email'
    ]
    raw_id_fields = ['user', 'institution']
    ordering = ['institution', 'user__last_name']
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'get_email'),
            'description': 'Información del usuario asociado'
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
            'description': 'Un tutor inactivo no podrá acceder al sistema'
        }),
        ('Estadísticas', {
            'fields': ('get_courses_count', 'get_students_count'),
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
            'description': 'Se creará un nuevo usuario con rol de Tutor'
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
    
    def get_courses_count(self, obj):
        return obj.get_courses_count()
    get_courses_count.short_description = 'Cursos'
    
    def get_students_count(self, obj):
        return obj.get_students_count()
    get_students_count.short_description = 'Estudiantes'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creación
            # Crear usuario
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', ''),
            )
            obj.user = user
            obj.created_by = request.user
            
            # Guardar el perfil
            obj.save()
            
            # Crear Membership con rol tutor
            Membership.objects.get_or_create(
                user=user,
                institution=obj.institution,
                defaults={
                    'role': 'tutor',
                    'is_active': obj.status == 'active'
                }
            )
        else:
            obj.save()
            # Sincronizar estado con Membership
            Membership.objects.filter(
                user=obj.user,
                institution=obj.institution,
                role='tutor'
            ).update(is_active=obj.status == 'active')
    
    actions = ['activate_tutors', 'deactivate_tutors', 'suspend_tutors']
    
    @admin.action(description='Activar tutores seleccionados')
    def activate_tutors(self, request, queryset):
        for tutor in queryset:
            tutor.activate()
        self.message_user(request, f'{queryset.count()} tutor(es) activado(s).')
    
    @admin.action(description='Desactivar tutores seleccionados')
    def deactivate_tutors(self, request, queryset):
        for tutor in queryset:
            tutor.deactivate()
        self.message_user(request, f'{queryset.count()} tutor(es) desactivado(s).')
    
    @admin.action(description='Suspender tutores seleccionados')
    def suspend_tutors(self, request, queryset):
        queryset.update(status='suspended')
        for tutor in queryset:
            Membership.objects.filter(
                user=tutor.user,
                institution=tutor.institution,
                role='tutor'
            ).update(is_active=False)
        self.message_user(request, f'{queryset.count()} tutor(es) suspendido(s).')


class TutorProfileInline(admin.StackedInline):
    """Inline para ver/editar TutorProfile desde el User admin"""
    model = TutorProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Tutor'
    fk_name = 'user'
    extra = 0
    readonly_fields = ['created_at', 'updated_at', 'created_by']


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1
    raw_id_fields = ['institution']


class StudentInline(admin.StackedInline):
    model = Student
    can_delete = False
    verbose_name_plural = 'Perfil de Estudiante'
    fk_name = 'user'


class CustomUserAdmin(BaseUserAdmin):
    inlines = (MembershipInline, TutorProfileInline, StudentInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_roles', 'get_tutor_profile', 'get_student_profile')
    
    def get_roles(self, obj):
        memberships = Membership.objects.filter(user=obj, is_active=True)
        if not memberships.exists():
            if obj.is_superuser:
                return "Superuser"
            return "Sin rol"
        roles = [f"{m.get_role_display()} ({m.institution.name[:20]})" for m in memberships[:3]]
        if memberships.count() > 3:
            roles.append(f"...+{memberships.count() - 3}")
        return ", ".join(roles)
    get_roles.short_description = 'Roles'
    
    def get_tutor_profile(self, obj):
        if hasattr(obj, 'tutor_profile'):
            return f"✓ {obj.tutor_profile.institution.name[:15]}"
        return "-"
    get_tutor_profile.short_description = 'Tutor'
    
    def get_student_profile(self, obj):
        if hasattr(obj, 'student_profile'):
            return obj.student_profile.student_id
        return "-"
    get_student_profile.short_description = 'ID Estudiante'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'user', 'course', 'get_institution', 'is_active', 'get_projects_count']
    list_filter = ['course__institution', 'course', 'is_active', 'created_at']
    search_fields = ['student_id', 'user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'get_projects_count']
    raw_id_fields = ['user', 'course']
    
    def get_institution(self, obj):
        return obj.institution.name if obj.institution else "-"
    get_institution.short_description = 'Institución'
    
    def get_projects_count(self, obj):
        return obj.get_projects_count()
    get_projects_count.short_description = 'Proyectos'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'student', 'get_course', 'get_institution', 'created_at', 'updated_at', 'is_active']
    list_filter = ['student__course__institution', 'student__course', 'is_active', 'created_at']
    search_fields = ['name', 'student__user__username', 'student__student_id']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['student']
    
    def get_course(self, obj):
        return obj.student.course.name if obj.student.course else "-"
    get_course.short_description = 'Curso'
    
    def get_institution(self, obj):
        return obj.institution.name if obj.institution else "-"
    get_institution.short_description = 'Institución'
    
    fieldsets = (
        ('Información General', {
            'fields': ('student', 'name', 'description', 'is_active')
        }),
        ('Contenido', {
            'fields': ('xml_content', 'arduino_code'),
            'classes': ('wide',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'status', 'deadline', 'allow_resubmit', 'published_at', 'created_at']
    list_filter = ['status', 'allow_resubmit', 'deadline', 'created_at', 'course__institution']
    search_fields = ['title', 'objective', 'instructions', 'course__name']
    readonly_fields = ['created_at', 'updated_at', 'published_at', 'get_submissions_count', 'get_pending_submissions_count']
    raw_id_fields = ['course']
    date_hierarchy = 'deadline'
    
    fieldsets = (
        ('Información General', {
            'fields': ('course', 'title', 'objective', 'instructions')
        }),
        ('Configuración', {
            'fields': ('deadline', 'status', 'allow_resubmit')
        }),
        ('Estadísticas', {
            'fields': ('get_submissions_count', 'get_pending_submissions_count'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_submissions_count(self, obj):
        return obj.get_submissions_count()
    get_submissions_count.short_description = 'Entregas'
    
    def get_pending_submissions_count(self, obj):
        return obj.get_pending_submissions_count()
    get_pending_submissions_count.short_description = 'Pendientes'


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'activity', 'attempt', 'status', 'submitted_at', 'get_institution']
    list_filter = ['status', 'submitted_at', 'created_at', 'activity__course__institution']
    search_fields = ['student__username', 'student__email', 'activity__title']
    readonly_fields = ['created_at', 'updated_at', 'submitted_at']
    raw_id_fields = ['activity', 'student']
    date_hierarchy = 'submitted_at'
    
    def get_institution(self, obj):
        return obj.institution.name if obj.institution else "-"
    get_institution.short_description = 'Institución'


@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    list_display = ['activity', 'get_total_max_score', 'created_at']
    list_filter = ['created_at', 'activity__course__institution']
    search_fields = ['activity__title', 'activity__course__name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['activity']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['submission', 'tutor', 'score', 'get_percentage_score', 'created_at', 'get_institution']
    list_filter = ['created_at', 'submission__activity__course__institution']
    search_fields = ['submission__student__username', 'submission__activity__title', 'tutor__username']
    readonly_fields = ['created_at', 'updated_at', 'get_percentage_score']
    raw_id_fields = ['submission', 'tutor']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información', {
            'fields': ('submission', 'tutor')
        }),
        ('Calificación', {
            'fields': ('score', 'comments', 'rubric_breakdown')
        }),
        ('Estadísticas', {
            'fields': ('get_percentage_score',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_percentage_score(self, obj):
        return f"{obj.get_percentage_score():.1f}%" if obj.get_percentage_score() else "-"
    get_percentage_score.short_description = 'Porcentaje'
    
    def get_institution(self, obj):
        return obj.institution.name if obj.institution else "-"
    get_institution.short_description = 'Institución'


@admin.register(IDEProject)
class IDEProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'institution', 'updated_at', 'get_institution', 'is_frozen']
    list_filter = ['created_at', 'updated_at', 'institution']
    search_fields = ['name', 'owner__username', 'owner__email', 'institution__name']
    readonly_fields = ['created_at', 'updated_at', 'get_last_modified', 'is_frozen']
    raw_id_fields = ['owner', 'institution']
    date_hierarchy = 'updated_at'
    
    def get_institution(self, obj):
        return obj.institution.name if obj.institution else "-"
    get_institution.short_description = 'Institución'
    
    def is_frozen(self, obj):
        return obj.is_frozen()
    is_frozen.boolean = True
    is_frozen.short_description = 'Congelado'


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
    list_display = ['activity', 'student', 'project', 'status', 'frozen_at', 'get_institution']
    list_filter = ['status', 'frozen_at', 'created_at', 'activity__course__institution']
    search_fields = ['activity__title', 'student__username', 'student__email', 'project__name']
    readonly_fields = ['created_at', 'updated_at', 'frozen_at']
    raw_id_fields = ['activity', 'student', 'project']
    date_hierarchy = 'created_at'
    
    def get_institution(self, obj):
        return obj.institution.name if obj.institution else "-"
    get_institution.short_description = 'Institución'


@admin.register(AgentInstance)
class AgentInstanceAdmin(admin.ModelAdmin):
    list_display = ['hostname', 'institution', 'os', 'agent_version', 'status', 'last_seen', 'is_online_display']
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
    
    def is_online_display(self, obj):
        return obj.is_online()
    is_online_display.boolean = True
    is_online_display.short_description = 'Online'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['actor', 'institution', 'action', 'entity', 'entity_id', 'ts']
    list_filter = ['action', 'entity', 'ts', 'institution']
    search_fields = ['actor__username', 'actor__email', 'entity', 'entity_id', 'institution__name']
    readonly_fields = ['ts']
    raw_id_fields = ['actor', 'institution']
    date_hierarchy = 'ts'
    
    fieldsets = (
        ('Acción', {
            'fields': ('actor', 'institution', 'action')
        }),
        ('Entidad', {
            'fields': ('entity', 'entity_id')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Fecha', {
            'fields': ('ts',)
        }),
    )


@admin.register(ErrorEvent)
class ErrorEventAdmin(admin.ModelAdmin):
    list_display = ['code', 'severity', 'institution', 'user', 'resolved', 'ts']
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


# Configuración del admin site
admin.site.site_header = "MAX-IDE Administración"
admin.site.site_title = "MAX-IDE Admin"
admin.site.index_title = "Panel de Administración"
