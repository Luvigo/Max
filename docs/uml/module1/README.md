# Módulo 1: Auth + Roles

## Descripción
Sistema de autenticación y autorización basado en roles para MAX-IDE.

## Roles Disponibles

| Rol | Descripción | Redirect Post-Login |
|-----|-------------|---------------------|
| `admin` | Administrador Global | `/admin/` (Django Admin) |
| `institution` | Admin de Institución | `/i/<slug>/dashboard/` |
| `tutor` | Tutor/Docente | `/i/<slug>/dashboard/tutor/` |
| `student` | Estudiante | `/i/<slug>/dashboard/student/` |

## Reglas Clave

### ⚠️ Admin NO tiene templates custom
El administrador (superuser/staff) utiliza **exclusivamente** el panel de Django Admin (`/admin/`).
No se crean dashboards personalizados para el rol admin.

### Flujo de Login
1. Usuario ingresa credenciales en `/login/`
2. Si es admin/staff → Redirige a `/admin/login/`
3. Si es usuario normal:
   - Se autentica y hace login
   - Se determina su rol desde `Membership`
   - Se redirige según rol e institución

### Decorators Disponibles

```python
from editor.mixins import (
    admin_required,      # Solo superuser/staff
    tutor_required,      # admin, institution, tutor
    student_required,    # Cualquier rol con membresía
    institution_admin_required,  # admin, institution
    role_required,       # Roles personalizados
)

# Uso
@tutor_required
def my_tutor_view(request):
    ...

@student_required
def my_student_view(request):
    ...
```

### Middleware
El `TenantMiddleware` añade al request:
- `request.current_institution`: Institución actual (desde URL `/i/<slug>/`)
- `request.current_membership`: Membresía del usuario en la institución
- `request.user_role`: Rol del usuario (`admin`, `institution`, `tutor`, `student`)
- `request.user_institutions`: QuerySet de instituciones del usuario

## Diagramas UML

- `use_cases.puml`: Casos de uso del módulo
- `sequence_auth.puml`: Flujo de autenticación
- `class_diagram.puml`: Diagrama de clases

## Errores Manejados

| Error | Código | Descripción |
|-------|--------|-------------|
| Credenciales inválidas | - | Mensaje en login |
| Acceso denegado | 403 | Template `403.html` |
| Sin rol asignado | - | Redirect al IDE básico |
| Sin institución | - | Redirect a selector |

## Archivos Relacionados

- `editor/auth_views.py`: Vistas de login/logout
- `editor/mixins.py`: Decorators y mixins
- `editor/middleware.py`: TenantMiddleware
- `editor/models.py`: Membership, UserRoleHelper
- `editor/templates/editor/login.html`: Template de login
- `editor/templates/editor/403.html`: Página de acceso denegado
