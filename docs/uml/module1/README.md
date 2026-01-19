# Módulo 1: Multi-tenant + RBAC + Dashboards

## Descripción
Este módulo implementa el sistema de autenticación basado en roles (RBAC) con soporte multi-tenant para MAX-IDE.

## Roles del Sistema

| Rol | Descripción | Permisos |
|-----|-------------|----------|
| `admin` | Administrador Global | Acceso total al sistema |
| `institution` | Admin de Institución | Gestión de su institución |
| `tutor` | Tutor/Profesor | Ver sus cursos y estudiantes |
| `student` | Estudiante | Ver sus proyectos |

## Estructura de URLs

```
/login/                          # Login general
/logout/                         # Cerrar sesión
/dashboard/                      # Redirige según rol
/select-institution/             # Selector de institución
/dashboard/admin/                # Dashboard admin global

# URLs con tenant (institución)
/i/<slug>/dashboard/             # Dashboard institución
/i/<slug>/dashboard/tutor/       # Dashboard tutor
/i/<slug>/dashboard/student/     # Dashboard estudiante
```

## Archivos Principales

### Backend
- `editor/models.py` - Modelos Institution, Membership, Course, Student, Project
- `editor/middleware.py` - TenantMiddleware para resolución de tenant
- `editor/mixins.py` - Mixins y decorators para RBAC
- `editor/dashboard_views.py` - Vistas de dashboards
- `editor/context_processors.py` - Variables globales para templates
- `editor/tests.py` - Tests unitarios

### Frontend
- `templates/base_dashboard.html` - Layout principal
- `templates/partials/sidebar.html` - Barra lateral
- `templates/partials/topbar.html` - Barra superior
- `templates/partials/alerts.html` - Sistema de alertas
- `templates/dashboards/` - Dashboards por rol

## Diagramas UML

### Casos de Uso
![Use Cases](./use_cases.puml)

### Diagrama de Clases
![Class Diagram](./class_diagram.puml)

### Secuencia de Autenticación
![Auth Sequence](./sequence_auth.puml)

## Middleware de Tenant

El `TenantMiddleware` añade al request:

```python
request.current_institution  # Institution actual (desde URL)
request.current_membership   # Membership del usuario en la institución
request.user_role           # Rol del usuario (admin, institution, tutor, student)
request.user_institutions   # QuerySet de instituciones del usuario
```

## Mixins Disponibles

```python
# Decorators para function-based views
@login_required_with_institution
@role_required('admin', 'institution')
@institution_required

# Mixins para class-based views
class MyView(InstitutionScopedMixin, TemplateView):
    pass

class MyView(AdminRequiredMixin, TemplateView):
    allowed_roles = ['admin']
```

## Tests

Ejecutar tests del módulo:
```bash
python manage.py test editor.tests
```

## Cache-busting

El sistema incluye un BUILD_ID que se imprime en:
- Atributo `data-build-id` en `<html>`
- Footer del dashboard
- Console del navegador

```javascript
console.log('[MAX-IDE] Build: dev-2026.01.19');
```
