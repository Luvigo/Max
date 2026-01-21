# Módulo 2: Estructura Académica Multi-tenant

## Descripción

Este módulo implementa la gestión académica completa con soporte multi-tenant, permitiendo a las instituciones gestionar cursos, asignar tutores y matricular estudiantes de forma independiente y segura.

## Componentes

### Modelos

- **Course**: Curso con `grade_level` y `status`
- **Enrollment**: Matrícula de estudiante en curso
- **TeachingAssignment**: Asignación de tutor a curso

### Vistas

#### Institución
- Lista de cursos
- Crear/Editar curso
- Asignar tutores
- Matricular estudiantes
- Importar CSV de estudiantes

#### Tutor
- Ver cursos asignados
- Ver roster del curso

#### Estudiante
- Ver cursos matriculados

### Seguridad

- **Cross-tenant protection**: Todas las operaciones verifican que los recursos pertenezcan a la institución del usuario
- **Role-based access**: Cada vista verifica los permisos según el rol
- **Tenant scoping**: URLs con formato `/i/<slug>/...`

## Diagramas UML

- `use_cases.puml`: Casos de uso del módulo
- `class_diagram.puml`: Diagrama de clases
