# Módulo 4: Integración MAX-IDE con Workspaces

## Descripción

Este módulo integra el MAX-IDE directamente en el contexto de actividades, permitiendo a los estudiantes trabajar en sus proyectos desde la actividad y a los tutores revisar entregas en modo read-only o usar un sandbox para probar actividades.

## Componentes

### Modelos

- **IDEProject**: Proyecto del IDE con owner, institution, blockly_xml, arduino_code
- **ProjectSnapshot**: Instantáneas del proyecto para versionado
- **ActivityWorkspace**: Relación entre actividad, estudiante y proyecto con control de estado (frozen/in_progress)

### Vistas

#### Estudiante
- Abrir IDE desde actividad con contexto completo
- Autosave automático del workspace
- Botón de entregar integrado
- Workspace se congela automáticamente después de entregar (si no se permite re-entrega)

#### Tutor
- Sandbox para probar actividades antes de publicarlas
- Ver IDE en modo read-only de entregas de estudiantes

### APIs

- `api_ide_autosave`: Autosave automático con prevención de conflictos
- `api_ide_create_snapshot`: Crear snapshots del proyecto
- `api_ide_load_project`: Cargar proyecto del IDE

### Seguridad

- **Cross-tenant protection**: Todos los proyectos verifican pertenencia a institución
- **Read-only enforcement**: Workspaces frozen no pueden editarse
- **Concurrency control**: Prevención de conflictos con transacciones
- **Permission checks**: Solo el owner puede editar su proyecto

### Estados y Reglas

- **In Progress**: Workspace activo, se puede editar
- **Frozen**: Workspace congelado (read-only) cuando:
  - Se entregó y no se permite re-entrega
  - La actividad está cerrada
  - Pasó el deadline
  
- **Sandbox**: Proyecto del tutor para probar actividades (siempre editable)

### Validaciones

- XML corrupto: Manejo de errores y fallback
- Conflicto de guardado: Prevención con transacciones y unique constraints
- Edición en modo read-only: Bloqueado en frontend y backend

## Diagramas UML

- `use_cases.puml`: Casos de uso del módulo
- `class_diagram.puml`: Diagrama de clases
