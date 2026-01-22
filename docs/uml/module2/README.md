# Módulo 2: Institución como Entidad Informativa

## Descripción
La institución es una entidad informativa en MAX-IDE. Todo el CRUD de instituciones se realiza exclusivamente desde Django Admin (`/admin/`).

## ⚠️ Regla Clave
**NO se crean vistas/templates de admin para instituciones.** Todo CRUD vive en Django Admin.

Tutor y Estudiante solo tienen acceso **read-only** a la información de su institución.

## Modelo Institution

### Campos Principales
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | str | Nombre de la institución |
| `slug` | str | Slug para URLs |
| `code` | str | Código único |
| `description` | str | Descripción |
| `logo` | URL | Logo de la institución |
| `status` | str | active/inactive/suspended |

### Campos de Contacto (nuevos)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `email` | str | Email de contacto |
| `phone` | str | Teléfono |
| `website` | URL | Sitio web |

### Campos de Dirección (nuevos)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `address` | str | Dirección |
| `city` | str | Ciudad |
| `state` | str | Estado/Provincia |
| `country` | str | País (default: México) |
| `postal_code` | str | Código Postal |

### Métodos
```python
institution.get_members_count()   # Total miembros
institution.get_tutors_count()    # Total tutores
institution.get_students_count()  # Total estudiantes
institution.get_courses_count()   # Total cursos
institution.get_tutors()          # QuerySet de tutores
institution.get_students()        # QuerySet de estudiantes
institution.get_full_address()    # Dirección formateada
```

## Vistas Read-Only

### URLs
| Ruta | Vista | Descripción |
|------|-------|-------------|
| `/i/<slug>/my-institution/` | `my_institution` | Vista genérica |
| `/i/<slug>/tutor/my-institution/` | `tutor_my_institution` | Vista de tutor |
| `/i/<slug>/student/my-institution/` | `student_my_institution` | Vista de estudiante |

### Templates
- `editor/institution/my_institution.html` - Vista genérica
- `editor/institution/tutor_institution.html` - Vista de tutor
- `editor/institution/student_institution.html` - Vista de estudiante

## Django Admin

### Configuración de InstitutionAdmin
```python
list_display = ['name', 'code', 'city', 'status', 'get_tutors_count', 'get_students_count', 'get_courses_count']
list_filter = ['status', 'country', 'city', 'created_at']
search_fields = ['name', 'code', 'slug', 'email', 'city', 'address']
```

### Acciones Disponibles
- `activate_institutions`: Activar instituciones seleccionadas
- `deactivate_institutions`: Desactivar instituciones seleccionadas

### Fieldsets
1. **Información General**: name, slug, code, description, logo
2. **Información de Contacto**: email, phone, website
3. **Dirección**: address, city, state, country, postal_code
4. **Estado**: status, is_active
5. **Configuración del Agent**: agent_token
6. **Estadísticas**: conteos de miembros, tutores, estudiantes, cursos
7. **Fechas**: created_at, updated_at

## Permisos

| Rol | Permiso |
|-----|---------|
| Admin | CRUD completo en `/admin/` |
| Institution | Solo lectura (my_institution) |
| Tutor | Solo lectura (tutor_my_institution) |
| Estudiante | Solo lectura (student_my_institution) |

## Diagramas UML
- `use_cases.puml`: Casos de uso del módulo
- `class_diagram.puml`: Diagrama de clases

## Archivos Relacionados
- `editor/models.py`: Modelo Institution
- `editor/admin.py`: InstitutionAdmin
- `editor/institution_views.py`: Vistas read-only
- `editor/templates/editor/institution/`: Templates
