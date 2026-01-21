# Módulo 3: Actividades, Entregas, Rúbricas y Feedback

## Descripción

Este módulo implementa el sistema completo de actividades y entregas con soporte multi-tenant, permitiendo a los tutores crear y gestionar actividades, y a los estudiantes entregar sus trabajos y recibir feedback.

## Componentes

### Modelos

- **Activity**: Actividad con estados (draft, published, closed), deadline y opción de re-entrega
- **Submission**: Entrega de estudiante con control de intentos y estados (pending, submitted, graded)
- **Rubric**: Rúbrica de evaluación con criterios en JSON
- **Feedback**: Calificación y comentarios del tutor con desglose por rúbrica

### Vistas

#### Tutor
- Lista de actividades del curso
- Crear/Editar actividad
- Publicar actividad
- Ver entregas de una actividad
- Calificar entrega

#### Estudiante
- Ver actividades del curso
- Ver detalle de actividad
- Entregar actividad
- Ver feedback de entrega

### Seguridad

- **Cross-tenant protection**: Todas las operaciones verifican pertenencia a la institución
- **Role-based access**: Solo tutores pueden crear/calificar, solo estudiantes pueden entregar
- **Concurrencia**: Prevención de doble submit con unique constraints y transacciones
- **Validaciones**: Verificación de estado publicado, deadline, re-entrega permitida

## Validaciones

- Actividad debe estar publicada para entregar
- No puede entregar si pasó el deadline
- Re-entrega solo si está permitida
- Prevención de doble submit (unique constraint + transaction)

## Diagramas UML

- `use_cases.puml`: Casos de uso del módulo
- `class_diagram.puml`: Diagrama de clases
