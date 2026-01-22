# Módulo 4: Grupos y Estudiantes

## Descripción
El tutor gestiona grupos y estudiantes desde la plataforma (templates).
El admin supervisa desde Django Admin (`/admin/`).

## ⚠️ Regla Clave
- **Tutor**: CRUD completo de grupos y estudiantes en templates.
- **Admin**: Solo supervisa desde Django Admin, NO hay templates de admin.
- **Estudiante**: Solo vista read-only de su contexto.

## Modelos

### StudentGroup
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | ID único |
| `institution` | FK(Institution) | Institución del grupo |
| `tutor` | FK(User) | Tutor responsable |
| `name` | str | Nombre del grupo |
| `code` | str | Código único (institution + code) |
| `description` | str | Descripción |
| `academic_year` | str | Año académico |
| `semester` | str | Semestre/Período |
| `status` | str | active/inactive/archived |
| `max_students` | int | Capacidad máxima |
| `created_by` | FK(User) | Creador |

### Student (extendido)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `user` | OneToOne(User) | Usuario asociado |
| `student_id` | str | Matrícula única |
| `institution` | FK(Institution) | Institución directa |
| `group` | FK(StudentGroup) | Grupo asignado |
| `tutor` | FK(User) | Tutor asignado |
| `course` | FK(Course) | Curso |
| `phone` | str | Teléfono |
| `emergency_contact` | str | Contacto de emergencia |
| `emergency_phone` | str | Teléfono de emergencia |
| `notes` | str | Notas internas |
| `is_active` | bool | Estado |
| `created_by` | FK(User) | Creador |

## URLs del Tutor

### Grupos
| URL | Vista | Descripción |
|-----|-------|-------------|
| `/i/<slug>/tutor/groups/` | `tutor_groups_list` | Lista de grupos |
| `/i/<slug>/tutor/groups/new/` | `tutor_group_create` | Crear grupo |
| `/i/<slug>/tutor/groups/<id>/` | `tutor_group_detail` | Detalle de grupo |
| `/i/<slug>/tutor/groups/<id>/edit/` | `tutor_group_edit` | Editar grupo |
| `/i/<slug>/tutor/groups/<id>/delete/` | `tutor_group_delete` | Eliminar/Archivar |

### Estudiantes
| URL | Vista | Descripción |
|-----|-------|-------------|
| `/i/<slug>/tutor/students/` | `tutor_students_list` | Lista de estudiantes |
| `/i/<slug>/tutor/students/new/` | `tutor_student_create` | Crear estudiante |
| `/i/<slug>/tutor/students/<id>/` | `tutor_student_detail` | Detalle de estudiante |
| `/i/<slug>/tutor/students/<id>/edit/` | `tutor_student_edit` | Editar estudiante |
| `/api/tutor/assign-group/` | `tutor_assign_student_to_group` | API AJAX |

## URLs del Estudiante

| URL | Vista | Descripción |
|-----|-------|-------------|
| `/i/<slug>/student/my-info/` | `student_my_context` | Ver mi información |

## Segregación de Datos

### Tutor
- Solo ve/edita grupos donde `tutor=request.user`
- Solo ve/edita estudiantes donde:
  - `tutor=request.user` O
  - `group__tutor=request.user`
- No puede ver grupos/estudiantes de otros tutores

### Estudiante
- Solo ve su propia información
- Ve datos de su grupo (nombre, compañeros)
- Ve datos de su tutor

## Django Admin

### StudentGroupAdmin
```python
list_display = ['name', 'code', 'institution', 'tutor', 'academic_year', 
                'status', 'students_count', 'max_students', 'available_slots']
list_filter = ['status', 'institution', 'academic_year', 'tutor']
actions = ['activate_groups', 'deactivate_groups', 'archive_groups']
```

### StudentAdmin
```python
list_display = ['student_id', 'user', 'full_name', 'institution', 'group', 
                'tutor', 'course', 'is_active', 'projects_count']
list_filter = ['is_active', 'institution', 'group', 'tutor', 'course']
actions = ['activate_students', 'deactivate_students']
```

## Templates

### Tutor
- `tutor/groups_list.html` - Lista de grupos con filtros
- `tutor/group_form.html` - Crear/Editar grupo
- `tutor/group_detail.html` - Detalle con lista de estudiantes
- `tutor/students_list.html` - Lista de estudiantes con filtros
- `tutor/student_create.html` - Crear estudiante (User + Student + Membership)
- `tutor/student_detail.html` - Detalle con reasignación de grupo
- `tutor/student_edit.html` - Editar estudiante

### Estudiante
- `student/my_context.html` - Ver mi información, grupo, tutor, compañeros

## Flujos

### Crear Estudiante (Tutor)
1. Tutor llena formulario (username, email, password, datos personales)
2. Se crea `User`
3. Se crea `Student` con `institution`, `group`, `tutor`
4. Se crea `Membership` con `role='student'`
5. Estudiante puede hacer login

### Asignar Grupo (Tutor)
1. Desde detalle de estudiante o lista
2. Seleccionar grupo (solo grupos del tutor)
3. Verificar capacidad
4. Actualizar `student.group`

## Diagramas UML
- `use_cases.puml`: Casos de uso
- `class_diagram.puml`: Diagrama de clases

## Archivos Relacionados
- `editor/models.py`: StudentGroup, Student (extendido)
- `editor/admin.py`: StudentGroupAdmin, StudentAdmin
- `editor/group_views.py`: Vistas de tutor y estudiante
- `editor/urls.py`: Rutas
- `editor/templates/editor/tutor/` - Templates de tutor
- `editor/templates/editor/student/my_context.html` - Template de estudiante
