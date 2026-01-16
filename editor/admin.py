from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Institution, Course, Student, Project


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'institution', 'academic_year', 'is_active', 'get_students_count']
    list_filter = ['institution', 'academic_year', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'institution__name']
    readonly_fields = ['created_at', 'updated_at', 'get_students_count']
    
    def get_students_count(self, obj):
        return obj.get_students_count()
    get_students_count.short_description = 'Estudiantes'


class StudentInline(admin.StackedInline):
    model = Student
    can_delete = False
    verbose_name_plural = 'Perfil de Estudiante'
    fk_name = 'user'


class CustomUserAdmin(BaseUserAdmin):
    inlines = (StudentInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_student_profile')
    
    def get_student_profile(self, obj):
        if hasattr(obj, 'student_profile'):
            return obj.student_profile.student_id
        return "No es estudiante"
    get_student_profile.short_description = 'ID Estudiante'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'user', 'course', 'is_active', 'get_projects_count']
    list_filter = ['course', 'is_active', 'created_at']
    search_fields = ['student_id', 'user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'get_projects_count']
    
    def get_projects_count(self, obj):
        return obj.get_projects_count()
    get_projects_count.short_description = 'Proyectos'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'student', 'created_at', 'updated_at', 'is_active']
    list_filter = ['student__course', 'is_active', 'created_at']
    search_fields = ['name', 'student__user__username', 'student__student_id']
    readonly_fields = ['created_at', 'updated_at']
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
