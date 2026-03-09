# Batería de Tests Funcionales - Tutor y Estudiante

## Requisito: SQLite o PostgreSQL

Estos tests funcionan con **SQLite** (por defecto) gracias a la migración `0010_sqlite_uuid_compat`, que convierte Institution y Membership a UUID en SQLite. También pueden ejecutarse con PostgreSQL si se configura `DATABASE_URL`:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/max_db"
python manage.py test editor.tests.test_tutor_views editor.tests.test_student_views editor.tests.test_role_permissions editor.tests.test_navigation_links editor.tests.test_activity_submission_flow editor.tests.test_smoke_flow
```

## Estructura de tests

```
editor/tests/
├── test_factories.py          # Helpers: create_institution, create_tutor, create_student, etc.
├── test_tutor_views.py        # Vistas del tutor
├── test_student_views.py      # Vistas del estudiante
├── test_role_permissions.py   # Permisos por rol
├── test_navigation_links.py   # Navegación, enlaces, NoReverseMatch
├── test_activity_submission_flow.py  # Flujo actividades y entregas
├── test_smoke_flow.py         # Smoke tests end-to-end
└── TESTS_TUTOR_STUDENT_README.md
```

## Cómo ejecutar los tests

### Todos los tests de Tutor y Estudiante (con PostgreSQL)

```bash
python manage.py test editor.tests.test_tutor_views editor.tests.test_student_views editor.tests.test_role_permissions editor.tests.test_navigation_links editor.tests.test_activity_submission_flow editor.tests.test_smoke_flow
```

### Solo tests de Tutor
```bash
python manage.py test editor.tests.test_tutor_views
```

### Solo tests de Estudiante
```bash
python manage.py test editor.tests.test_student_views
```

### Solo tests de permisos
```bash
python manage.py test editor.tests.test_role_permissions
```

### Smoke flow completo
```bash
python manage.py test editor.tests.test_smoke_flow
```

### Desde la raíz del proyecto (con PostgreSQL configurado)
```bash
cd /ruta/al/proyecto
export DATABASE_URL="postgresql://user:password@localhost:5432/max_db"  # si no está ya configurado
python manage.py test editor.tests.test_tutor_views editor.tests.test_student_views editor.tests.test_role_permissions editor.tests.test_navigation_links editor.tests.test_activity_submission_flow editor.tests.test_smoke_flow
```

### Con SQLite (por defecto)
Sin `DATABASE_URL`, Django usa SQLite. Los tests se ejecutan correctamente gracias a la migración `0010_sqlite_uuid_compat`.

## Cobertura funcional lograda

### Tutor
- ✅ Dashboard carga (200), secciones Mis Grupos, Métricas
- ✅ Lista y detalle de grupos
- ✅ Crear/editar grupo
- ✅ Lista de estudiantes, crear estudiante, detalle
- ✅ Lista de actividades, crear actividad, ver entregas
- ✅ Detalle y calificación de entrega
- ✅ Ver bloques de entrega (IDE read-only)
- ✅ IDE sandbox (si existe, sin 500)

### Estudiante
- ✅ Dashboard carga, muestra grupo, tutor, actividades
- ✅ Lista de actividades del grupo
- ✅ Detalle de actividad
- ✅ IDE de actividad con botón Entregar
- ✅ Entrega vía API (submit)
- ✅ Submission visible para tutor

### Permisos
- ✅ Anónimo redirigido al login
- ✅ Tutor no ve grupos/entregas de otro tutor
- ✅ Estudiante no accede a vistas del tutor
- ✅ Tutor no califica entregas ajenas

### Navegación
- ✅ assertContains para textos clave (Ver todos, Nuevo Estudiante, Entregar, etc.)
- ✅ reverse() sin NoReverseMatch en URLs principales

### Smoke flow
- ✅ Flujo Tutor: login → grupos → crear grupo → estudiantes → actividades
- ✅ Flujo Estudiante: login → dashboard → actividad → IDE → entregar → tutor ve

## Bugs / advertencias detectadas

- ~~**WARNING**: `urls.W005` - URL namespace 'editor' no es único.~~ (Corregido: urls_global sin app_name)
- **WARNING**: `Bad Request` en `/api/activity/.../submit/` en algunos tests (posible CSRF o Content-Type).
- ~~**Not Found**: Rutas de detalle/edición de grupos~~ (Corregido: URLs usan `{% url %}` con `group_id` UUID; 404 solo cuando el tutor intenta acceder a grupo de otro tutor).

## Notas

- No se prueba Agent Local ni WebSerial real
- No se usan sleeps ni dependencias externas
- Los tests usan `TestCase` y `Client` de Django
- Fixtures creadas en código vía `test_factories.py`
