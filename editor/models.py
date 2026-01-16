from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Institution(models.Model):
    """Institución educativa"""
    name = models.CharField(max_length=200, verbose_name="Nombre")
    code = models.CharField(max_length=50, unique=True, verbose_name="Código")
    description = models.TextField(blank=True, verbose_name="Descripción")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    
    class Meta:
        verbose_name = "Institución"
        verbose_name_plural = "Instituciones"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Course(models.Model):
    """Curso o Grupo"""
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='courses', verbose_name="Institución")
    name = models.CharField(max_length=200, verbose_name="Nombre del Curso")
    code = models.CharField(max_length=50, verbose_name="Código")
    description = models.TextField(blank=True, verbose_name="Descripción")
    academic_year = models.CharField(max_length=20, default="2024-2025", verbose_name="Año Académico")
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
        return self.students.count()


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
        return self.projects.count()


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
