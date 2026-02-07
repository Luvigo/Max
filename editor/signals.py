"""
Señales para garantizar integridad de perfiles según roles.

Cuando un usuario obtiene rol ESTUDIANTE o TUTOR vía Membership, se auto-crea
el perfil correspondiente (Student / TutorProfile) para que aparezca en Django Admin.

Decisión de negocio: Si el usuario cambia de estudiante a tutor (o viceversa),
NO se borra el perfil anterior. Solo se crea el nuevo si no existe.
Esto evita pérdida de datos y mantiene historial.
"""
import uuid as uuid_module
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Membership, Student, TutorProfile


def ensure_profile_for_membership(membership, created_by=None):
    """
    Garantiza que exista Student o TutorProfile según el rol de la membresía.
    
    - Si role == 'student' y no existe Student para ese user => crea Student
    - Si role == 'tutor' y no existe TutorProfile para ese user => crea TutorProfile
    
    No duplica perfiles. No borra perfiles existentes.
    
    Args:
        membership: instancia de Membership guardada
        created_by: User que realizó la acción (opcional, para auditoría)
    """
    if membership.role == 'student':
        # Usar .exists() en lugar de hasattr: hasattr(user, 'student_profile')
        # puede fallar si el reverse OneToOne no existe (RelatedObjectDoesNotExist)
        if not Student.objects.filter(user=membership.user).exists():
            student_id = f"EST-{membership.user.id}-{str(uuid_module.uuid4())[:4].upper()}"
            Student.objects.create(
                user=membership.user,
                student_id=student_id,
                institution=membership.institution,
                is_active=membership.is_active,
                created_by=created_by,
            )
    
    elif membership.role == 'tutor':
        # TutorProfile tiene OneToOne con User: un usuario solo puede tener un TutorProfile.
        # Verificamos por user (no por institution) para no duplicar.
        if not TutorProfile.objects.filter(user=membership.user).exists():
            TutorProfile.objects.create(
                user=membership.user,
                institution=membership.institution,
                status='active' if membership.is_active else 'inactive',
                created_by=created_by,
            )


@receiver(post_save, sender=Membership)
def membership_post_save_ensure_profile(sender, instance, created, **kwargs):
    """
    Al guardar una Membership, garantiza que exista el perfil correspondiente.
    
    Cubre: creación desde admin, edición desde admin, creación/edición desde
    API, shell, fixtures, etc. created_by queda None cuando se invoca desde
    señal (no hay request.user disponible).
    """
    ensure_profile_for_membership(instance, created_by=None)
