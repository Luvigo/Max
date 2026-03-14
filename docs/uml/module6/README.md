# Módulo 6: Operaciones Globales (Django Admin)

## Descripción
Todas las operaciones de administración global se realizan EXCLUSIVAMENTE desde Django Admin (`/admin/`).
NO se crean templates ni rutas tipo `/admin-panel/`.

## Funcionalidades

### 1. list_display Mejorado
Cada modelo muestra información relevante con badges de colores:
- Estados con colores semafóricos (verde=activo, amarillo=pendiente, rojo=error)
- Contadores de relaciones (estudiantes, actividades, entregas)
- Fechas con indicadores visuales

### 2. search_fields Avanzado
Búsqueda en múltiples campos:
- Usernames, emails, nombres completos
- Nombres de instituciones, grupos, cursos
- Códigos y IDs

### 3. list_filter Personalizado
Filtros predefinidos:
- `IsActiveListFilter`: Filtra por estado de cuenta de usuario
- `HasSubmissionsFilter`: Filtra actividades con/sin entregas
- `DeadlineStatusFilter`: Filtra por estado de fecha límite

### 4. Acciones Masivas

#### Usuarios/Tutores/Estudiantes
- ✅ Activar seleccionados
- ⏸️ Desactivar seleccionados
- 🚫 Suspender seleccionados
- 🔒 Deshabilitar cuentas de usuario

#### Instituciones/Grupos/Cursos
- ✅ Activar
- ⏸️ Desactivar
- 📦 Archivar

#### Actividades
- ✅ Publicar
- 🔒 Cerrar
- 📝 Pasar a borrador

#### Entregas
- ✅ Marcar como calificadas
- 📨 Marcar como entregadas
- 👁️ Marcar como revisadas
- 🔄 Resetear a en progreso

#### Errores
- ✅ Marcar como resueltos
- 🔄 Marcar como pendientes

### 5. Exportación CSV
Disponible en todos los modelos principales:
- Seleccionar registros
- Acción "📥 Exportar seleccionados a CSV"
- Descarga archivo con todos los campos

### 6. Auditoría
Campos automáticos en modelos clave:
- `created_at`: Fecha de creación
- `updated_at`: Fecha de actualización
- `created_by`: Usuario que creó el registro

## Mixins

### ExportCSVMixin
```python
class ExportCSVMixin:
    def export_as_csv(self, request, queryset):
        # Genera CSV con todos los campos del modelo
```

### AuditMixin
```python
class AuditMixin:
    def save_model(self, request, obj, form, change):
        # Guarda automáticamente created_by
```

## Filtros Personalizados

### IsActiveListFilter
Filtra por estado de cuenta de usuario (activo/inactivo)

### HasSubmissionsFilter
Filtra actividades con o sin entregas

### DeadlineStatusFilter
- Próximas (7 días)
- Vencidas
- Sin fecha límite

## Archivos
- `editor/admin.py`: Configuración completa del admin
- `docs/uml/module6/`: Documentación UML

## Acceso
```
URL: /admin/
Usuario: Superusuario o staff
```

## Badges Visuales
Los badges usan colores consistentes:
- 🟢 Verde (#2ea043): Activo, OK, Calificado
- 🟡 Amarillo (#e3b341): Pendiente, En progreso, Advertencia
- 🔴 Rojo (#f85149): Error, Suspendido, Vencido
- 🔵 Azul (#58a6ff): Info, Entregado, Tutor
- 🟣 Púrpura (#a371f7): Institución, Especial
- ⚪ Gris (#8b949e): Inactivo, Offline
