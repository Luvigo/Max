# Modulo 4: Grupos y Estudiantes

## Descripcion
El tutor gestiona grupos y estudiantes desde la plataforma (templates).
El admin supervisa desde Django Admin (/admin/).

## Regla Clave
- Tutor: CRUD completo de grupos y estudiantes en templates.
- Admin: Solo supervisa desde Django Admin, NO hay templates de admin.
- Estudiante: Solo vista read-only de su contexto.

## Modelos

### StudentGroup
- id: UUID
- institution: FK(Institution)
- tutor: FK(User)
- name, code, description
- academic_year, semester
- status: active/inactive/archived
- max_students: int
- created_by: FK(User)

### Student (extendido)
- user: OneToOne(User)
- student_id: str (unico)
- institution: FK(Institution)
- group: FK(StudentGroup)
- tutor: FK(User)
- course: FK(Course)
- phone, emergency_contact, emergency_phone
- notes, is_active
- created_by: FK(User)

## URLs del Tutor

### Grupos
- /i/slug/tutor/groups/ - Lista
- /i/slug/tutor/groups/new/ - Crear
- /i/slug/tutor/groups/id/ - Detalle
- /i/slug/tutor/groups/id/edit/ - Editar
- /i/slug/tutor/groups/id/delete/ - Eliminar

### Estudiantes
- /i/slug/tutor/students/ - Lista
- /i/slug/tutor/students/new/ - Crear
- /i/slug/tutor/students/id/ - Detalle
- /i/slug/tutor/students/id/edit/ - Editar

## URLs del Estudiante
- /i/slug/student/my-info/ - Ver mi informacion

## Segregacion de Datos

### Tutor
- Solo ve/edita grupos donde tutor=request.user
- Solo ve/edita estudiantes donde tutor=request.user O group__tutor=request.user

### Estudiante
- Solo ve su propia informacion
- Ve datos de su grupo y tutor

## Django Admin
- StudentGroupAdmin con filtros por institucion, tutor, estado
- StudentAdmin con filtros por institucion, grupo, tutor

## Archivos
- editor/models.py: StudentGroup, Student
- editor/admin.py: StudentGroupAdmin, StudentAdmin
- editor/group_views.py: Vistas
- editor/urls.py: Rutas
- editor/templates/editor/tutor/ - Templates tutor
- editor/templates/editor/student/my_context.html - Template estudiante
