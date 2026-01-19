from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify


class Institution(models.Model):
    """Institución educativa - Tenant principal"""
    name = models.CharField(max_length=200, verbose_name="Nombre")
    slug = models.SlugField(max_length=100, unique=True, blank=True, verbose_name="Slug URL")
    code = models.CharField(max_length=50, unique=True, verbose_name="Código")
    description = models.TextField(blank=True, verbose_name="Descripción")
    logo = models.URLField(blank=True, verbose_name="Logo URL")
    
    # Status
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('inactive', 'Inactiva'),
        ('suspended', 'Suspendida'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Estado")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Legacy field - mantener compatibilidad
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    
    class Meta:
        verbose_name = "Institución"
        verbose_name_plural = "Instituciones"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Asegurar slug único
            original_slug = self.slug
            counter = 1
            while Institution.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        # Sincronizar is_active con status
        self.is_active = (self.status == 'active')
        super().save(*args, **kwargs)
    
    def get_members_count(self):
        return self.memberships.filter(is_active=True).count()
    
    def get_courses_count(self):
        return self.courses.filter(is_active=True).count()
    
    def get_students_count(self):
        return self.memberships.filter(role='student', is_active=True).count()


class Membership(models.Model):
    """Membresía de usuario a institución con rol"""
    
    ROLE_CHOICES = [
        ('admin', 'Administrador Global'),
        ('institution', 'Administrador de Institución'),
        ('tutor', 'Tutor'),
        ('student', 'Estudiante'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships', verbose_name="Usuario")
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='memberships', verbose_name="Institución")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', verbose_name="Rol")
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata opcional
    notes = models.TextField(blank=True, verbose_name="Notas")
    
    class Meta:
        verbose_name = "Membresía"
        verbose_name_plural = "Membresías"
        unique_together = ['user', 'institution']
        ordering = ['institution', 'role', 'user__username']
    
    def __str__(self):
        return f"{self.user.username} - {self.institution.name} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_institution_admin(self):
        return self.role in ('admin', 'institution')
    
    @property
    def is_tutor_or_above(self):
        return self.role in ('admin', 'institution', 'tutor')
    
    @property
    def is_student(self):
        return self.role == 'student'


class Course(models.Model):
    """Curso o Grupo"""
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='courses', verbose_name="Institución")
    name = models.CharField(max_length=200, verbose_name="Nombre del Curso")
    code = models.CharField(max_length=50, verbose_name="Código")
    description = models.TextField(blank=True, verbose_name="Descripción")
    academic_year = models.CharField(max_length=20, default="2024-2025", verbose_name="Año Académico")
    
    # Tutor asignado
    tutor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='tutored_courses',
        verbose_name="Tutor"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['institution', 'academic_year', 'name']
        unique_together = ['institution', 'code', 'academic_year']
    
    def __str__(self):
        return f"{self.name} - {self.institution.name}"
    
    def get_students_count(self):
        return self.students.filter(is_active=True).count()


class Student(models.Model):
    """Perfil de Estudiante"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile', verbose_name="Usuario")
    student_id = models.CharField(max_length=50, unique=True, verbose_name="ID de Estudiante")
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name="Curso")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        ordering = ['student_id']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.student_id})"
    
    def get_projects_count(self):
        return self.projects.filter(is_active=True).count()
    
    @property
    def institution(self):
        """Obtener institución del estudiante vía curso"""
        if self.course:
            return self.course.institution
        return None


class Project(models.Model):
    """Proyecto de Arduino"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='projects', verbose_name="Estudiante")
    name = models.CharField(max_length=200, verbose_name="Nombre del Proyecto")
    description = models.TextField(blank=True, verbose_name="Descripción")
    xml_content = models.TextField(blank=True, verbose_name="Contenido XML (Blockly)")
    arduino_code = models.TextField(blank=True, verbose_name="Código Arduino")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} - {self.student.user.username}"
    
    def get_last_modified(self):
        return self.updated_at.strftime("%d/%m/%Y %H:%M")
    
    @property
    def institution(self):
        """Obtener institución del proyecto vía estudiante"""
        if self.student and self.student.course:
            return self.student.course.institution
        return None


# ============================================
# HELPERS Y MANAGERS
# ============================================

class UserRoleHelper:
    """Helper para obtener información de roles de usuario"""
    
    @staticmethod
    def get_user_role(user, institution=None):
        """Obtener el rol del usuario en una institución específica o el rol más alto"""
        if not user.is_authenticated:
            return None
        
        # Superuser siempre es admin
        if user.is_superuser:
            return 'admin'
        
        memberships = Membership.objects.filter(user=user, is_active=True)
        
        if institution:
            membership = memberships.filter(institution=institution).first()
            return membership.role if membership else None
        
        # Sin institución específica, retornar el rol más alto
        role_priority = {'admin': 0, 'institution': 1, 'tutor': 2, 'student': 3}
        best_role = None
        best_priority = 999
        
        for m in memberships:
            if role_priority.get(m.role, 999) < best_priority:
                best_priority = role_priority[m.role]
                best_role = m.role
        
        return best_role
    
    @staticmethod
    def get_user_institutions(user):
        """Obtener todas las instituciones del usuario"""
        if not user.is_authenticated:
            return Institution.objects.none()
        
        if user.is_superuser:
            return Institution.objects.filter(status='active')
        
        return Institution.objects.filter(
            memberships__user=user,
            memberships__is_active=True,
            status='active'
        ).distinct()
    
    @staticmethod
    def user_has_role(user, roles, institution=None):
        """Verificar si el usuario tiene alguno de los roles especificados"""
        if isinstance(roles, str):
            roles = [roles]
        
        current_role = UserRoleHelper.get_user_role(user, institution)
        return current_role in roles
    
    @staticmethod
    def get_single_institution(user):
        """Si el usuario solo pertenece a una institución, retornarla"""
        institutions = UserRoleHelper.get_user_institutions(user)
        if institutions.count() == 1:
            return institutions.first()
        return None
