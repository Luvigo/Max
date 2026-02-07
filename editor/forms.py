"""
Formularios para el Módulo 2: Estructura Académica
Formularios para el Módulo 3: Actividades y Entregas
"""
from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    Course, Enrollment, TeachingAssignment, Institution, Membership,
    Activity, Submission, Rubric, Feedback, StudentGroup
)


def _institution_from_value(value, queryset):
    """Resuelve valor a Institution: acepta UUID (pk) o institution.code."""
    import uuid as uuid_module
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    raw = str(value).strip()
    try:
        uuid_module.UUID(raw)
        return queryset.filter(pk=raw).first()
    except (ValueError, TypeError):
        return queryset.filter(code=raw).first()


class InstitutionIdOrCodeField(forms.ModelChoiceField):
    """
    ModelChoiceField que acepta UUID (pk) o institution.code.
    Fix para raw_id_fields cuando el usuario ingresa el código en vez del UUID.
    """
    def to_python(self, value):
        if value in self.empty_values:
            return None
        inst = _institution_from_value(value, self.queryset)
        if inst:
            return inst
        raise forms.ValidationError(
            self.error_messages['invalid_choice'],
            code='invalid_choice',
            params={'value': value},
        )


class StudentGroupAdminForm(forms.ModelForm):
    """Formulario para Grupos de Estudiantes en Django Admin. Acepta institution por UUID o por code."""
    institution = InstitutionIdOrCodeField(queryset=Institution.objects.all())

    class Meta:
        model = StudentGroup
        fields = '__all__'


class CourseForm(forms.ModelForm):
    """Formulario para crear/editar cursos"""
    
    class Meta:
        model = Course
        fields = ['name', 'code', 'description', 'grade_level', 'status', 'academic_year']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Matemáticas 1ro A'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: MAT-1A-2024'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del curso...'
            }),
            'grade_level': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1ro, 2do, Bachillerato'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'academic_year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2024-2025'
            }),
        }
        labels = {
            'name': 'Nombre del Curso',
            'code': 'Código',
            'description': 'Descripción',
            'grade_level': 'Nivel de Grado',
            'status': 'Estado',
            'academic_year': 'Año Académico',
        }


class AssignTutorForm(forms.Form):
    """Formulario para asignar tutores a un curso"""
    tutor = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tutor',
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        institution = kwargs.pop('institution', None)
        super().__init__(*args, **kwargs)
        
        if institution:
            # Solo tutores que pertenecen a la institución
            tutors = User.objects.filter(
                memberships__institution=institution,
                memberships__role__in=['tutor', 'institution', 'admin'],
                memberships__is_active=True
            ).distinct()
            self.fields['tutor'].queryset = tutors


class EnrollmentForm(forms.ModelForm):
    """Formulario para matricular estudiantes"""
    
    class Meta:
        model = Enrollment
        fields = ['student', 'status', 'notes']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notas opcionales...'
            }),
        }
        labels = {
            'student': 'Estudiante',
            'status': 'Estado',
            'notes': 'Notas',
        }
    
    def __init__(self, *args, **kwargs):
        institution = kwargs.pop('institution', None)
        super().__init__(*args, **kwargs)
        
        if institution:
            # Solo estudiantes que pertenecen a la institución
            students = User.objects.filter(
                memberships__institution=institution,
                memberships__role='student',
                memberships__is_active=True
            ).distinct()
            self.fields['student'].queryset = students


class CSVImportForm(forms.Form):
    """Formulario para importar estudiantes desde CSV"""
    csv_file = forms.FileField(
        label='Archivo CSV',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        help_text='Archivo CSV con columnas: username, email, first_name, last_name, student_id (opcional)'
    )
    
    def clean_csv_file(self):
        file = self.cleaned_data.get('csv_file')
        if file:
            if not file.name.endswith('.csv'):
                raise forms.ValidationError('El archivo debe ser un CSV (.csv)')
            if file.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('El archivo es demasiado grande (máximo 5MB)')
        return file


# ============================================
# MÓDULO 3: ACTIVIDADES Y ENTREGAS
# ============================================

class ActivityForm(forms.ModelForm):
    """Formulario para crear/editar actividades"""
    
    class Meta:
        model = Activity
        fields = ['title', 'objective', 'instructions', 'deadline', 'status', 'allow_resubmit']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Control de LED con Arduino'
            }),
            'objective': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Objetivo de la actividad...'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Instrucciones detalladas para los estudiantes...'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'allow_resubmit': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título',
            'objective': 'Objetivo',
            'instructions': 'Instrucciones',
            'deadline': 'Fecha Límite',
            'status': 'Estado',
            'allow_resubmit': 'Permitir Re-entrega',
        }
    
    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < timezone.now():
            raise forms.ValidationError('La fecha límite no puede ser en el pasado')
        return deadline


class SubmissionForm(forms.ModelForm):
    """Formulario para entregar una actividad"""
    
    class Meta:
        model = Submission
        fields = ['artifact_ref']
        widgets = {
            'artifact_ref': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        self.activity = kwargs.pop('activity', None)
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        
        if self.activity:
            # Validar que la actividad esté publicada
            if not self.activity.is_published():
                raise forms.ValidationError('La actividad no está publicada')
            
            # Validar que no haya pasado el deadline
            if self.activity.is_deadline_passed():
                raise forms.ValidationError('La fecha límite ya pasó')
    
    def clean(self):
        cleaned_data = super().clean()
        artifact_ref = cleaned_data.get('artifact_ref')
        
        if not artifact_ref or not artifact_ref.get('project_id'):
            raise forms.ValidationError('Debes seleccionar un proyecto para entregar')
        
        return cleaned_data
    
    def save(self, commit=True):
        submission = super().save(commit=False)
        submission.activity = self.activity
        submission.student = self.student
        submission.status = 'submitted'
        submission.submitted_at = timezone.now()
        
        if commit:
            # Obtener el siguiente intento
            last_submission = Submission.objects.filter(
                activity=self.activity,
                student=self.student
            ).order_by('-attempt').first()
            
            if last_submission:
                submission.attempt = last_submission.attempt + 1
            else:
                submission.attempt = 1
            
            submission.save()
        
        return submission


class RubricForm(forms.ModelForm):
    """Formulario para crear/editar rúbricas"""
    
    class Meta:
        model = Rubric
        fields = ['criteria']
        widgets = {
            'criteria': forms.HiddenInput(),
        }


class FeedbackForm(forms.ModelForm):
    """Formulario para calificar una entrega"""
    
    class Meta:
        model = Feedback
        fields = ['score', 'comments', 'rubric_breakdown']
        widgets = {
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ej: 8.5'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Comentarios sobre la entrega...'
            }),
            'rubric_breakdown': forms.HiddenInput(),
        }
        labels = {
            'score': 'Puntaje',
            'comments': 'Comentarios',
            'rubric_breakdown': 'Desglose de Rúbrica',
        }
    
    def __init__(self, *args, **kwargs):
        self.submission = kwargs.pop('submission', None)
        self.tutor = kwargs.pop('tutor', None)
        super().__init__(*args, **kwargs)
        
        if self.submission and self.submission.activity.rubric:
            rubric = self.submission.activity.rubric
            max_score = rubric.get_total_max_score()
            if max_score:
                self.fields['score'].widget.attrs['max'] = str(max_score)
    
    def clean_score(self):
        score = self.cleaned_data.get('score')
        if score is not None:
            if self.submission and self.submission.activity.rubric:
                max_score = self.submission.activity.rubric.get_total_max_score()
                if score > max_score:
                    raise forms.ValidationError(f'El puntaje no puede ser mayor a {max_score}')
                if score < 0:
                    raise forms.ValidationError('El puntaje no puede ser negativo')
        return score
    
    def save(self, commit=True):
        feedback = super().save(commit=False)
        feedback.submission = self.submission
        feedback.tutor = self.tutor
        
        if commit:
            feedback.save()
            # Actualizar estado de la entrega
            self.submission.status = 'graded'
            self.submission.save()
        
        return feedback
