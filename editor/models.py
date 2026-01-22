from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
import uuid
import json

# JSONField nativo de Django (disponible desde Django 3.1+)
# Si usas Django < 3.1, cambia a django.contrib.postgres.fields.JSONField
try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField


class Institution(models.Model):
    """
    MÓDULO 2: Institución educativa - Tenant principal
    
    La institución es una entidad informativa. Todo CRUD se hace desde Django Admin.
    Tutor/Estudiante solo tienen vistas read-only.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="Nombre")
    slug = models.SlugField(max_length=100, unique=True, blank=True, verbose_name="Slug URL")
    code = models.CharField(max_length=50, unique=True, verbose_name="Código")
    description = models.TextField(blank=True, verbose_name="Descripción")
    logo = models.URLField(blank=True, verbose_name="Logo URL")
    
    # Información de contacto (MÓDULO 2)
    email = models.EmailField(blank=True, verbose_name="Email de contacto")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")
    website = models.URLField(blank=True, verbose_name="Sitio web")
    
    # Dirección (MÓDULO 2)
    address = models.CharField(max_length=300, blank=True, verbose_name="Dirección")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ciudad")
    state = models.CharField(max_length=100, blank=True, verbose_name="Estado/Provincia")
    country = models.CharField(max_length=100, default="México", verbose_name="País")
    postal_code = models.CharField(max_length=20, blank=True, verbose_name="Código Postal")
    
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
    
    # Token para registro de Agents
    agent_token = models.CharField(max_length=64, blank=True, null=True, verbose_name="Token de Agent", help_text="Token para que los Agents se registren")
    
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
        
        # Generar token de agent si no existe
        if not self.agent_token:
            import secrets
            self.agent_token = secrets.token_urlsafe(32)
        
        super().save(*args, **kwargs)
    
    def generate_new_agent_token(self):
        """Generar un nuevo token para agents"""
        import secrets
        self.agent_token = secrets.token_urlsafe(32)
        self.save(update_fields=['agent_token'])
        return self.agent_token
    
    def get_members_count(self):
        return self.memberships.filter(is_active=True).count()
    
    def get_courses_count(self):
        return self.courses.filter(is_active=True).count()
    
    def get_students_count(self):
        return self.memberships.filter(role='student', is_active=True).count()
    
    def get_tutors_count(self):
        """Obtener número de tutores activos"""
        return self.memberships.filter(role='tutor', is_active=True).count()
    
    def get_tutors(self):
        """Obtener lista de tutores de la institución"""
        from django.contrib.auth.models import User
        return User.objects.filter(
            memberships__institution=self,
            memberships__role='tutor',
            memberships__is_active=True
        ).distinct()
    
    def get_students(self):
        """Obtener lista de estudiantes de la institución"""
        from django.contrib.auth.models import User
        return User.objects.filter(
            memberships__institution=self,
            memberships__role='student',
            memberships__is_active=True
        ).distinct()
    
    def get_full_address(self):
        """Obtener dirección completa formateada"""
        parts = [self.address, self.city, self.state, self.postal_code, self.country]
        return ", ".join(p for p in parts if p)


class Membership(models.Model):
    """Membresía de usuario a institución con rol"""
    
    ROLE_CHOICES = [
        ('admin', 'Administrador Global'),
        ('institution', 'Administrador de Institución'),
        ('tutor', 'Tutor'),
        ('student', 'Estudiante'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    
    # Nivel de grado (ej: "1ro", "2do", "3ro", "Bachillerato", etc.)
    grade_level = models.CharField(max_length=50, blank=True, verbose_name="Nivel de Grado")
    
    # Estado del curso
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Estado")
    
    # Tutor asignado (legacy - mantener para compatibilidad)
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
        """Obtener número de estudiantes matriculados activos"""
        return self.enrollments.filter(status='active').count()
    
    def get_enrolled_students(self):
        """Obtener estudiantes matriculados activos"""
        return User.objects.filter(
            enrollments__course=self,
            enrollments__status='active'
        ).distinct()
    
    def get_assigned_tutors(self):
        """Obtener tutores asignados activos"""
        return User.objects.filter(
            teaching_assignments__course=self,
            teaching_assignments__status='active'
        ).distinct()


class Enrollment(models.Model):
    """Matrícula de estudiante en un curso"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments', verbose_name="Curso")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments', verbose_name="Estudiante")
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('completed', 'Completado'),
        ('dropped', 'Abandonado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Estado")
    
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Matrícula")
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, verbose_name="Notas")
    
    class Meta:
        verbose_name = "Matrícula"
        verbose_name_plural = "Matrículas"
        unique_together = ['course', 'student']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.name}"
    
    @property
    def institution(self):
        """Obtener institución del curso"""
        return self.course.institution


class TeachingAssignment(models.Model):
    """Asignación de tutor a un curso"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='teaching_assignments', verbose_name="Curso")
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teaching_assignments', verbose_name="Tutor")
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('completed', 'Completado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Estado")
    
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Asignación")
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, verbose_name="Notas")
    
    class Meta:
        verbose_name = "Asignación de Tutor"
        verbose_name_plural = "Asignaciones de Tutores"
        unique_together = ['course', 'tutor']
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.tutor.username} - {self.course.name}"
    
    @property
    def institution(self):
        """Obtener institución del curso"""
        return self.course.institution


# ============================================
# MÓDULO 3: PERFIL DE TUTOR
# ============================================

class TutorProfile(models.Model):
    """
    MÓDULO 3: Perfil de Tutor
    
    El admin gestiona tutores EXCLUSIVAMENTE desde Django Admin (/admin/).
    NO hay rutas/templates tipo /admin-panel/tutors.
    El tutor solo tiene vista read-only de su perfil.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='tutor_profile', 
        verbose_name="Usuario"
    )
    institution = models.ForeignKey(
        'Institution', 
        on_delete=models.CASCADE, 
        related_name='tutors',
        verbose_name="Institución"
    )
    
    # Identificación
    employee_id = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="ID de Empleado",
        help_text="Número de empleado o identificador interno"
    )
    
    # Información profesional
    title = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Título",
        help_text="Ej: Profesor, Ing., Lic., Dr."
    )
    specialization = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name="Especialización",
        help_text="Área de especialización o materia"
    )
    bio = models.TextField(
        blank=True, 
        verbose_name="Biografía",
        help_text="Breve descripción profesional"
    )
    
    # Contacto
    phone = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")
    office = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Oficina",
        help_text="Ubicación de oficina o cubículo"
    )
    
    # Estado
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('on_leave', 'Licencia'),
        ('suspended', 'Suspendido'),
    ]
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active', 
        verbose_name="Estado"
    )
    
    # Auditoría
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tutors_created',
        verbose_name="Creado por",
        help_text="Administrador que creó el perfil"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    
    class Meta:
        verbose_name = "Perfil de Tutor"
        verbose_name_plural = "Perfiles de Tutores"
        ordering = ['institution', 'user__last_name', 'user__first_name']
        unique_together = ['user', 'institution']
    
    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        title = f"{self.title} " if self.title else ""
        return f"{title}{name} ({self.institution.name})"
    
    @property
    def is_active(self):
        """Verificar si el tutor está activo"""
        return self.status == 'active'
    
    @property
    def full_name(self):
        """Obtener nombre completo con título"""
        name = self.user.get_full_name() or self.user.username
        return f"{self.title} {name}".strip() if self.title else name
    
    @property
    def email(self):
        """Obtener email del usuario"""
        return self.user.email
    
    def get_courses_count(self):
        """Obtener número de cursos asignados activos"""
        return TeachingAssignment.objects.filter(
            tutor=self.user,
            course__institution=self.institution,
            status='active'
        ).count()
    
    def get_students_count(self):
        """Obtener número total de estudiantes en sus cursos"""
        assignments = TeachingAssignment.objects.filter(
            tutor=self.user,
            course__institution=self.institution,
            status='active'
        )
        total = 0
        for assignment in assignments:
            total += assignment.course.get_students_count()
        return total
    
    def get_courses(self):
        """Obtener cursos asignados"""
        return Course.objects.filter(
            teaching_assignments__tutor=self.user,
            teaching_assignments__status='active',
            institution=self.institution
        ).distinct()
    
    def can_login(self):
        """Verificar si el tutor puede hacer login"""
        return self.status == 'active' and self.user.is_active
    
    def deactivate(self, reason=''):
        """Desactivar tutor"""
        self.status = 'inactive'
        self.save()
        # También desactivar membresía
        Membership.objects.filter(
            user=self.user,
            institution=self.institution,
            role='tutor'
        ).update(is_active=False)
    
    def activate(self):
        """Activar tutor"""
        self.status = 'active'
        self.save()
        # También activar membresía
        Membership.objects.filter(
            user=self.user,
            institution=self.institution,
            role='tutor'
        ).update(is_active=True)


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
# MÓDULO 3: ACTIVIDADES Y ENTREGAS
# ============================================

class Activity(models.Model):
    """Actividad o tarea asignada a un curso"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='activities', verbose_name="Curso")
    
    title = models.CharField(max_length=200, verbose_name="Título")
    objective = models.TextField(blank=True, verbose_name="Objetivo")
    instructions = models.TextField(verbose_name="Instrucciones")
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Límite")
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('published', 'Publicada'),
        ('closed', 'Cerrada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Estado")
    allow_resubmit = models.BooleanField(default=False, verbose_name="Permitir Re-entrega")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Publicación")
    
    class Meta:
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"
        ordering = ['-deadline', '-created_at']
        indexes = [
            models.Index(fields=['course', 'status']),
            models.Index(fields=['deadline']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.course.name}"
    
    @property
    def institution(self):
        """Obtener institución del curso"""
        return self.course.institution
    
    def is_published(self):
        """Verificar si la actividad está publicada"""
        return self.status == 'published'
    
    def is_closed(self):
        """Verificar si la actividad está cerrada"""
        return self.status == 'closed'
    
    def is_deadline_passed(self):
        """Verificar si ya pasó la fecha límite"""
        if not self.deadline:
            return False
        return timezone.now() > self.deadline
    
    def get_submissions_count(self):
        """Obtener número de entregas"""
        return self.submissions.filter(status__in=['submitted', 'graded']).count()
    
    def get_pending_submissions_count(self):
        """Obtener número de entregas pendientes de calificar"""
        return self.submissions.filter(status='submitted').count()


class Submission(models.Model):
    """Entrega de un estudiante para una actividad"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='submissions', verbose_name="Actividad")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions', verbose_name="Estudiante")
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('submitted', 'Entregada'),
        ('graded', 'Calificada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Estado")
    
    attempt = models.IntegerField(default=1, verbose_name="Intento")
    artifact_ref = models.JSONField(default=dict, blank=True, verbose_name="Referencia al Artefacto")
    # artifact_ref puede contener: {"project_id": 123, "xml_content": "...", "arduino_code": "..."}
    
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Entrega")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Entrega"
        verbose_name_plural = "Entregas"
        unique_together = [['activity', 'student', 'attempt']]
        ordering = ['-submitted_at', '-created_at']
        indexes = [
            models.Index(fields=['activity', 'student']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.activity.title} (Intento {self.attempt})"
    
    @property
    def institution(self):
        """Obtener institución de la actividad"""
        return self.activity.institution
    
    def can_resubmit(self):
        """Verificar si puede re-entregar"""
        if not self.activity.allow_resubmit:
            return False
        if self.activity.is_closed():
            return False
        if self.activity.is_deadline_passed():
            return False
        return True
    
    def get_latest_feedback(self):
        """Obtener el feedback más reciente"""
        return self.feedbacks.order_by('-created_at').first()


class Rubric(models.Model):
    """Rúbrica de evaluación para una actividad"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.OneToOneField(Activity, on_delete=models.CASCADE, related_name='rubric', verbose_name="Actividad")
    
    # criteria es un JSON con la estructura de la rúbrica
    # Ejemplo: {
    #   "criteria": [
    #     {"name": "Funcionalidad", "weight": 0.4, "max_score": 10},
    #     {"name": "Código", "weight": 0.3, "max_score": 10},
    #     {"name": "Documentación", "weight": 0.3, "max_score": 10}
    #   ],
    #   "total_max_score": 10
    # }
    criteria = models.JSONField(default=dict, blank=True, verbose_name="Criterios")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Rúbrica"
        verbose_name_plural = "Rúbricas"
    
    def __str__(self):
        return f"Rúbrica - {self.activity.title}"
    
    @property
    def institution(self):
        """Obtener institución de la actividad"""
        return self.activity.institution
    
    def get_total_max_score(self):
        """Obtener el puntaje máximo total"""
        if not self.criteria or 'total_max_score' not in self.criteria:
            return 10  # Default
        return self.criteria.get('total_max_score', 10)


class Feedback(models.Model):
    """Feedback y calificación de una entrega"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='feedbacks', verbose_name="Entrega")
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks_given', verbose_name="Tutor")
    
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Puntaje")
    comments = models.TextField(blank=True, verbose_name="Comentarios")
    
    # rubric_breakdown contiene los puntajes por criterio según la rúbrica
    # Ejemplo: {
    #   "Funcionalidad": 8.5,
    #   "Código": 7.0,
    #   "Documentación": 9.0
    # }
    rubric_breakdown = models.JSONField(default=dict, blank=True, verbose_name="Desglose de Rúbrica")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['submission', 'tutor']),
        ]
    
    def __str__(self):
        return f"Feedback - {self.submission.student.username} - {self.submission.activity.title}"
    
    @property
    def institution(self):
        """Obtener institución de la entrega"""
        return self.submission.institution
    
    def get_percentage_score(self):
        """Obtener el puntaje como porcentaje"""
        if not self.score:
            return None
        rubric = self.submission.activity.rubric
        if rubric:
            max_score = rubric.get_total_max_score()
            if max_score > 0:
                return (float(self.score) / float(max_score)) * 100
        return None


# ============================================
# MÓDULO 4: IDE Y WORKSPACES
# ============================================

class IDEProject(models.Model):
    """Proyecto del IDE de Arduino"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ide_projects', verbose_name="Propietario")
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='ide_projects', verbose_name="Institución")
    
    name = models.CharField(max_length=200, verbose_name="Nombre del Proyecto")
    blockly_xml = models.TextField(blank=True, verbose_name="Contenido XML (Blockly)")
    arduino_code = models.TextField(blank=True, verbose_name="Código Arduino")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Modificación")
    
    class Meta:
        verbose_name = "Proyecto IDE"
        verbose_name_plural = "Proyectos IDE"
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['owner', 'institution']),
            models.Index(fields=['-updated_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.owner.username}"
    
    def get_last_modified(self):
        """Obtener fecha de última modificación formateada"""
        return self.updated_at.strftime("%d/%m/%Y %H:%M")
    
    def is_frozen(self):
        """Verificar si el proyecto está congelado (read-only)"""
        # Verificar si hay un workspace frozen asociado
        return self.activity_workspaces.filter(status='frozen').exists()


class ProjectSnapshot(models.Model):
    """Snapshot (instantánea) de un proyecto"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(IDEProject, on_delete=models.CASCADE, related_name='snapshots', verbose_name="Proyecto")
    
    label = models.CharField(max_length=200, blank=True, verbose_name="Etiqueta")
    blockly_xml = models.TextField(blank=True, verbose_name="Contenido XML (Blockly)")
    arduino_code = models.TextField(blank=True, verbose_name="Código Arduino")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    
    class Meta:
        verbose_name = "Snapshot de Proyecto"
        verbose_name_plural = "Snapshots de Proyectos"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', '-created_at']),
        ]
    
    def __str__(self):
        return f"Snapshot - {self.project.name} ({self.label or 'Sin etiqueta'})"
    
    @property
    def institution(self):
        """Obtener institución del proyecto"""
        return self.project.institution


class ActivityWorkspace(models.Model):
    """Workspace de actividad - relación entre actividad, estudiante y proyecto"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='workspaces', verbose_name="Actividad")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_workspaces', verbose_name="Estudiante")
    project = models.ForeignKey(IDEProject, on_delete=models.CASCADE, related_name='activity_workspaces', verbose_name="Proyecto")
    
    STATUS_CHOICES = [
        ('in_progress', 'En Progreso'),
        ('frozen', 'Congelado (Read-only)'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress', verbose_name="Estado")
    
    frozen_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Congelamiento")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Workspace de Actividad"
        verbose_name_plural = "Workspaces de Actividades"
        unique_together = [['activity', 'student']]
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['activity', 'student']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Workspace - {self.activity.title} - {self.student.username}"
    
    @property
    def institution(self):
        """Obtener institución de la actividad"""
        return self.activity.institution
    
    def is_frozen(self):
        """Verificar si el workspace está congelado"""
        return self.status == 'frozen'
    
    def freeze(self):
        """Congelar el workspace (read-only)"""
        if self.status != 'frozen':
            self.status = 'frozen'
            self.frozen_at = timezone.now()
            self.save()
    
    def unfreeze(self):
        """Descongelar el workspace (solo si allow_resubmit está permitido)"""
        if self.status == 'frozen' and self.activity.allow_resubmit:
            self.status = 'in_progress'
            self.frozen_at = None
            self.save()


# ============================================
# MÓDULO 5: AGENT LOCAL INSTITUCIONAL
# ============================================

class AgentInstance(models.Model):
    """Instancia de Agent Local registrada en el sistema"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='agent_instances', verbose_name="Institución")
    
    hostname = models.CharField(max_length=255, verbose_name="Hostname")
    os = models.CharField(max_length=100, verbose_name="Sistema Operativo")
    agent_version = models.CharField(max_length=50, verbose_name="Versión del Agent")
    ide_version_compatible = models.CharField(max_length=50, blank=True, verbose_name="Versión IDE Compatible")
    
    # Estado del Agent
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('error', 'Error'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline', verbose_name="Estado")
    
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name="Última Conexión")
    
    # Metadata adicional en JSON
    meta = models.JSONField(default=dict, blank=True, verbose_name="Metadata")
    # meta puede contener: {"ip": "...", "port": 8765, "arduino_cli_version": "...", "python_version": "..."}
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Instancia de Agent"
        verbose_name_plural = "Instancias de Agents"
        unique_together = [['institution', 'hostname']]
        ordering = ['-last_seen', '-created_at']
        indexes = [
            models.Index(fields=['institution', 'status']),
            models.Index(fields=['-last_seen']),
        ]
    
    def __str__(self):
        return f"{self.hostname} - {self.institution.name} ({self.get_status_display()})"
    
    def is_online(self):
        """Verificar si el agent está online"""
        if self.status != 'online':
            return False
        
        # Verificar si last_seen es reciente (últimos 2 minutos)
        if not self.last_seen:
            return False
        
        threshold = timezone.now() - timezone.timedelta(minutes=2)
        return self.last_seen > threshold
    
    def update_heartbeat(self):
        """Actualizar heartbeat del agent"""
        self.last_seen = timezone.now()
        self.status = 'online'
        self.save(update_fields=['last_seen', 'status', 'updated_at'])
    
    def mark_offline(self):
        """Marcar agent como offline"""
        if self.status == 'online':
            self.status = 'offline'
            self.save(update_fields=['status', 'updated_at'])
    
    def mark_error(self, error_message=None):
        """Marcar agent con error"""
        self.status = 'error'
        if error_message:
            if not self.meta:
                self.meta = {}
            self.meta['last_error'] = error_message
        self.save(update_fields=['status', 'meta', 'updated_at'])
    
    def get_info(self):
        """Obtener información del Agent para APIs"""
        return {
            'id': str(self.id),
            'hostname': self.hostname,
            'os': self.os,
            'status': self.status,
            'agent_version': self.agent_version,
            'ide_version_compatible': self.ide_version_compatible,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'meta': self.meta,
            'institution': {
                'id': str(self.institution.id),
                'name': self.institution.name,
                'slug': self.institution.slug,
            },
        }


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


class AuditLog(models.Model):
    """Log de auditoría de acciones del sistema"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Actor (usuario que realiza la acción)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs', verbose_name="Actor")
    
    # Institución (tenant)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='audit_logs', null=True, blank=True, verbose_name="Institución")
    
    # Acción realizada
    ACTION_CHOICES = [
        ('create', 'Crear'),
        ('update', 'Actualizar'),
        ('delete', 'Eliminar'),
        ('publish', 'Publicar'),
        ('submit', 'Entregar'),
        ('grade', 'Calificar'),
        ('enroll', 'Matricular'),
        ('assign', 'Asignar'),
        ('login', 'Iniciar Sesión'),
        ('logout', 'Cerrar Sesión'),
        ('access', 'Acceder'),
        ('export', 'Exportar'),
        ('import', 'Importar'),
    ]
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name="Acción")
    
    # Entidad afectada
    entity = models.CharField(max_length=100, verbose_name="Entidad", help_text="Nombre del modelo (ej: Course, Activity)")
    entity_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="ID de Entidad")
    
    # Metadata adicional en JSON
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadata")
    
    # Timestamp
    ts = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp", db_index=True)
    
    class Meta:
        verbose_name = "Log de Auditoría"
        verbose_name_plural = "Logs de Auditoría"
        ordering = ['-ts']
        indexes = [
            models.Index(fields=['-ts']),
            models.Index(fields=['institution', '-ts']),
            models.Index(fields=['actor', '-ts']),
            models.Index(fields=['entity', 'entity_id']),
        ]
    
    def __str__(self):
        actor_name = self.actor.username if self.actor else "Sistema"
        return f"{actor_name} - {self.get_action_display()} - {self.entity}"


class ErrorEvent(models.Model):
    """Eventos de error del sistema para observabilidad"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Institución (tenant)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='error_events', null=True, blank=True, verbose_name="Institución")
    
    # Usuario afectado (nullable para errores del sistema)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='error_events', verbose_name="Usuario")
    
    # Código del error
    ERROR_CODE_CHOICES = [
        ('BootloaderSyncFailed', 'BootloaderSyncFailed'),
        ('PortBusy', 'PortBusy'),
        ('AgentMissing', 'AgentMissing'),
        ('UploadFailed', 'UploadFailed'),
        ('WorkspaceCorrupt', 'WorkspaceCorrupt'),
        ('SubmissionRace', 'SubmissionRace'),
        ('CompilationError', 'CompilationError'),
        ('SerialError', 'SerialError'),
        ('AuthenticationError', 'AuthenticationError'),
        ('PermissionError', 'PermissionError'),
        ('ValidationError', 'ValidationError'),
        ('NetworkError', 'NetworkError'),
        ('GenericError', 'GenericError'),
    ]
    code = models.CharField(max_length=100, choices=ERROR_CODE_CHOICES, verbose_name="Código de Error")
    
    # Severidad
    SEVERITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium', verbose_name="Severidad")
    
    # Mensaje del error
    message = models.TextField(verbose_name="Mensaje")
    
    # Contexto adicional en JSON
    context = models.JSONField(default=dict, blank=True, verbose_name="Contexto")
    
    # Timestamp
    ts = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp", db_index=True)
    
    # Resolución (opcional)
    resolved = models.BooleanField(default=False, verbose_name="Resuelto")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Resuelto en")
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_errors', verbose_name="Resuelto por")
    
    class Meta:
        verbose_name = "Evento de Error"
        verbose_name_plural = "Eventos de Error"
        ordering = ['-ts']
        indexes = [
            models.Index(fields=['-ts']),
            models.Index(fields=['institution', '-ts']),
            models.Index(fields=['code', '-ts']),
            models.Index(fields=['severity', '-ts']),
            models.Index(fields=['resolved', '-ts']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.message[:50]} ({self.get_severity_display()})"
    
    def mark_resolved(self, user=None):
        """Marcar error como resuelto"""
        self.resolved = True
        self.resolved_at = timezone.now()
        if user:
            self.resolved_by = user
        self.save(update_fields=['resolved', 'resolved_at', 'resolved_by'])