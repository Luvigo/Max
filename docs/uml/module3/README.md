# Módulo 3: Gestión de Tutores

## Descripción
El admin gestiona tutores EXCLUSIVAMENTE desde Django Admin (`/admin/`).
NO hay rutas/templates tipo `/admin-panel/tutors`.

## ⚠️ Regla Clave
**Todo CRUD de TutorProfile se hace desde Django Admin.** El tutor solo tiene vista read-only de su perfil.

## Modelo TutorProfile

### Campos Principales
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `user` | OneToOne(User) | Usuario asociado |
| `institution` | FK(Institution) | Institución del tutor |
| `employee_id` | str | ID de empleado (opcional) |
| `title` | str | Título (Lic., Ing., Dr., etc.) |
| `specialization` | str | Área de especialización |
| `bio` | str | Biografía profesional |
| `phone` | str | Teléfono |
| `office` | str | Oficina/Cubículo |
| `status` | str | active/inactive/on_leave/suspended |
| `created_by` | FK(User) | Admin que creó el perfil |

### Estados
| Estado | Descripción | Puede Login |
|--------|-------------|-------------|
| `active` | Activo | ✓ |
| `inactive` | Inactivo | ✗ |
| `on_leave` | Licencia | ✗ |
| `suspended` | Suspendido | ✗ |

### Métodos
```python
tutor.is_active           # Property: status == 'active'
tutor.full_name           # Con título
tutor.email               # Del user
tutor.get_courses_count() # Cursos asignados activos
tutor.get_students_count() # Total estudiantes
tutor.get_courses()       # QuerySet de cursos
tutor.can_login()         # status=='active' AND user.is_active
tutor.activate()          # Activar tutor y membership
tutor.deactivate()        # Desactivar tutor y membership
```

## Django Admin

### TutorProfileAdmin
```python
list_display = ['full_name', 'user', 'institution', 'title', 'specialization', 'status', 'courses_count', 'students_count']
list_filter = ['status', 'institution', 'created_at']
search_fields = ['user__username', 'user__email', 'employee_id', 'institution__name', 'specialization']
```

### Crear Tutor (desde Admin)
1. Ir a `/admin/editor/tutorprofile/add/`
2. Llenar datos del usuario (username, email, password)
3. Seleccionar institución
4. Llenar información profesional
5. Guardar

**Automáticamente se crea:**
- User con los datos proporcionados
- TutorProfile vinculado al User
- Membership con rol='tutor'

### Acciones
| Acción | Descripción |
|--------|-------------|
| `activate_tutors` | Activa tutores seleccionados |
| `deactivate_tutors` | Desactiva tutores seleccionados |
| `suspend_tutors` | Suspende tutores seleccionados |

## Vista Read-Only del Tutor

### URL
```
/i/<slug>/tutor/profile/
```

### Template
`editor/templates/editor/tutor/profile.html`

### Contenido
- Información personal (solo lectura)
- Estadísticas (cursos, estudiantes)
- Lista de cursos asignados
- Información de la cuenta

### Decorador
```python
@login_required
@tutor_required
def tutor_profile(request, institution_slug):
    ...
```

## Bloqueo de Tutores Inactivos

### Middleware
El `TenantMiddleware` verifica el estado del tutor:

1. Si `TutorProfile.status != 'active'`
2. Si `Membership.is_active = False`

→ Se bloquea acceso a rutas `/tutor/*`
→ Se muestra mensaje de error
→ Se redirige al dashboard

### Rutas Exentas
- `/login/`
- `/logout/`
- `/admin/`
- `/static/`
- `/api/agent/`

## Permisos

| Actor | Acción | Permitido |
|-------|--------|-----------|
| Admin | CRUD TutorProfile | ✓ (en /admin/) |
| Admin | Activar/Desactivar | ✓ |
| Tutor | Ver su perfil | ✓ (read-only) |
| Tutor | Editar su perfil | ✗ |
| Student | Ver perfil tutor | ✗ |

## Diagramas UML
- `use_cases.puml`: Casos de uso
- `class_diagram.puml`: Diagrama de clases

## Archivos Relacionados
- `editor/models.py`: TutorProfile
- `editor/admin.py`: TutorProfileAdmin
- `editor/tutor_views.py`: Vista de perfil
- `editor/middleware.py`: Verificación de estado
- `editor/templates/editor/tutor/profile.html`: Template
