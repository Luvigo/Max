from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Institution, Membership, Course, Student, Project


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'code', 'status', 'get_members_count', 'get_courses_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'code', 'slug']
    readonly_fields = ['created_at', 'updated_at', 'get_members_count', 'get_courses_count']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Información General', {
            'fields': ('name', 'slug', 'code', 'description', 'logo')
        }),
        ('Estado', {
            'fields': ('status', 'is_active')
        }),
        ('Estadísticas', {
            'fields': ('get_members_count', 'get_courses_count'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_members_count(self, obj):
        return obj.get_members_count()
    get_members_count.short_description = 'Miembros'
    
    def get_courses_count(self, obj):
        return obj.get_courses_count()
    get_courses_count.short_description = 'Cursos'


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
    list_display = ['name', 'code', 'institution', 'tutor', 'academic_year', 'is_active', 'get_students_count']
    list_filter = ['institution', 'academic_year', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'institution__name', 'tutor__username']
    readonly_fields = ['created_at', 'updated_at', 'get_students_count']
    raw_id_fields = ['institution', 'tutor']
    
    def get_students_count(self, obj):
        return obj.get_students_count()
    get_students_count.short_description = 'Estudiantes'


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
    inlines = (MembershipInline, StudentInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_roles', 'get_student_profile')
    
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

# Configuración del admin site
admin.site.site_header = "MAX-IDE Administración"
admin.site.site_title = "MAX-IDE Admin"
admin.site.index_title = "Panel de Administración"
