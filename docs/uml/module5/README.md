# Modulo 5: Actividades y Entregas por Grupo

## Descripcion
- Tutor gestiona actividades desde templates
- Estudiante ve actividades de su grupo y entrega desde IDE
- Admin supervisa desde Django Admin (/admin/)

## Modelos

### Activity (extendido)
- id: UUID
- group: FK(StudentGroup) - actividad para un grupo
- course: FK(Course) - actividad para un curso (legacy)
- created_by: FK(User) - tutor creador
- title, objective, instructions
- deadline: datetime
- status: draft/published/closed
- allow_resubmit, allow_late_submit: bool
- max_score: decimal

### Submission (extendido)
- id: UUID
- activity: FK(Activity)
- student: FK(User)
- status: pending/in_progress/submitted/graded/returned
- attempt: int
- xml_content, arduino_code: text
- notes: text
- score: decimal
- is_late, is_read_only: bool
- graded_by: FK(User)
- submitted_at, graded_at: datetime

## URLs del Tutor

### Actividades por Grupo
- /i/slug/tutor/groups/id/activities/ - Lista
- /i/slug/tutor/groups/id/activities/new/ - Crear
- /i/slug/tutor/groups/id/activities/id/edit/ - Editar

### Entregas
- /i/slug/tutor/activities/id/submissions/ - Lista de entregas
- /i/slug/tutor/submissions/id/ - Detalle
- /i/slug/tutor/submissions/id/grade/ - Calificar

## URLs del Estudiante
- /i/slug/student/activities/ - Ver actividades de mi grupo
- /i/slug/student/activities/id/ - Detalle de actividad
- /i/slug/student/activities/id/ide/ - IDE para trabajar

## APIs
- POST /i/slug/api/activity/id/submit/ - Entregar actividad
- POST /i/slug/api/activity/id/save/ - Guardar progreso (autosave)

## Flujo de Entrega
1. Estudiante abre IDE -> crea Submission (in_progress)
2. Autosave guarda xml_content cada 3 segundos
3. Boton Entregar -> submit() -> status=submitted, is_read_only=True
4. IDE pasa a modo solo lectura
5. Tutor califica -> grade() -> status=graded

## Validaciones (can_submit)
- Actividad publicada
- Actividad no cerrada
- Dentro de fecha limite (o allow_late_submit)
- Estudiante pertenece al grupo
- No ha entregado antes (o allow_resubmit)

## Django Admin
- ActivityAdmin: filtros por grupo/curso/institucion, acciones publish/close/draft
- SubmissionAdmin: filtros por estado/fecha, acciones mark_as_graded/submitted

## Archivos
- editor/models.py: Activity, Submission (extendidos)
- editor/admin.py: ActivityAdmin, SubmissionAdmin
- editor/activity_group_views.py: Vistas
- editor/urls.py: Rutas
- editor/templates/editor/activity/tutor/ - Templates tutor
- editor/templates/editor/activity/student/ - Templates estudiante
