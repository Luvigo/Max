# MÓDULO 6: Observabilidad (ErrorEvent/AuditLog) + Dashboards por Rol

## Descripción

Este módulo implementa un sistema completo de observabilidad para el MAX-IDE, permitiendo registrar eventos de error y logs de auditoría con dashboards específicos por rol.

## Componentes Principales

### Modelos

#### `AuditLog`
Registra todas las acciones del sistema para auditoría:
- **Actor**: Usuario que realiza la acción
- **Institución**: Tenant asociado
- **Acción**: Tipo de acción (create, update, delete, publish, submit, grade, login, logout, access, export, import)
- **Entidad**: Modelo afectado (Course, Activity, etc.)
- **Entity ID**: ID de la entidad afectada
- **Metadata**: Información adicional en JSON
- **Timestamp**: Fecha y hora del evento

#### `ErrorEvent`
Registra eventos de error para observabilidad:
- **Institución**: Tenant asociado (opcional)
- **Usuario**: Usuario afectado (opcional, para errores del sistema)
- **Código**: Tipo de error (BootloaderSyncFailed, PortBusy, AgentMissing, UploadFailed, WorkspaceCorrupt, SubmissionRace, CompilationError, SerialError, etc.)
- **Severidad**: Nivel de severidad (low, medium, high, critical)
- **Mensaje**: Descripción del error
- **Contexto**: Información adicional en JSON (institution_slug, activity_id, project_id, agent_status, etc.)
- **Timestamp**: Fecha y hora del error
- **Resolución**: Campos para marcar errores como resueltos

## Funcionalidades

### APIs

#### `POST /api/errors/`
Registra un nuevo evento de error desde el frontend (IDE y dashboards).
- Permite registrar errores con código, severidad, mensaje y contexto
- Detecta automáticamente la institución del usuario
- Retorna el ID del error creado

#### `GET /api/errors/list/`
Lista errores filtrados por rol/tenant:
- **Admin**: Ve todos los errores
- **Institución**: Ve solo errores de su institución
- **Tutor**: Ve errores de sus cursos/actividades
- **Estudiante**: Solo diagnóstico propio

### Dashboards

#### Admin (`/admin-panel/errors/`)
- Lista global de todos los errores
- Estadísticas (total, resueltos, sin resolver, críticos)
- Filtros por código, severidad, estado
- Top errores por código
- Detalle de error con opción de marcar como resuelto

#### Institución (`/i/<slug>/institution/errors/`)
- Lista de errores de la institución
- Estadísticas (total, resueltos, sin resolver, últimas 24h)
- Agrupación por código de error
- Filtros por código, severidad, estado

#### Tutor (`/i/<slug>/tutor/errors/`)
- Lista de errores relacionados con sus cursos
- Estadísticas básicas
- Filtros por código y severidad

### Integración en IDE

#### Botón "Copiar Diagnóstico"
Permite copiar al portapapeles un diagnóstico completo del estado del IDE:
- Información de institución, actividad y proyecto
- Estado del Agent (URL, versión, plataforma)
- Estado de conexión y últimos errores
- Timestamp del diagnóstico

#### Botón "Reportar Error"
Permite reportar un error al backend con:
- Código de error seleccionado
- Descripción del error
- Contexto completo (institución, actividad, proyecto, estado del Agent, etc.)
- Severidad determinada automáticamente según el código

## Tipos de Error

Los siguientes tipos de error están definidos:
- `BootloaderSyncFailed`: Error de sincronización del bootloader
- `PortBusy`: Puerto ocupado
- `AgentMissing`: Agent no disponible
- `UploadFailed`: Fallo en la subida del código
- `WorkspaceCorrupt`: Workspace corrupto
- `SubmissionRace`: Condición de carrera en entrega
- `CompilationError`: Error de compilación
- `SerialError`: Error en comunicación serial
- `AuthenticationError`: Error de autenticación
- `PermissionError`: Error de permisos
- `ValidationError`: Error de validación
- `NetworkError`: Error de red
- `GenericError`: Error genérico

## Seguridad

- **Cross-tenant protection**: Los usuarios solo ven errores de su institución
- **Role-based access**: Cada rol tiene acceso a diferentes niveles de información
- **Audit trail**: Todas las acciones importantes se registran en `AuditLog`

## Diagramas UML

- `use_cases.puml`: Casos de uso del módulo
- `class_diagram.puml`: Diagrama de clases mostrando los modelos y sus relaciones

## Entregables

- ✅ Modelos `AuditLog` y `ErrorEvent` en `editor/models.py`
- ✅ APIs `/api/errors/` y `/api/errors/list/` en `editor/error_views.py`
- ✅ Vistas de dashboards por rol en `editor/error_views.py`
- ✅ Templates para dashboards de errores
- ✅ Integración en IDE (copiar diagnóstico, reportar error) en `app.js`
- ✅ URLs configuradas en `editor/urls.py` y `arduino_ide/urls.py`
- ✅ Modelos registrados en `editor/admin.py`
- ✅ Diagramas UML en `docs/uml/module6/`
