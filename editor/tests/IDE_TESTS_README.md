# Tests del IDE MAX-IDE

Batería de tests automáticos para comprobar el flujo del IDE: generación de código, compilación, subida y validaciones.

## Estructura de tests

| Archivo | Descripción |
|---------|-------------|
| `test_ide_code_generation.py` | Validación de generación y payloads de código |
| `test_ide_compile_flow.py` | Flujo de compilación y rechazo de código vacío |
| `test_ide_upload_preconditions.py` | Precondiciones de subida (board, port, code) |
| `test_ide_integration.py` | Integración mínima del flujo completo |
| `../agent/tests/test_agent_compile_mock.py` | Mocks del Agent (health, compile, upload) |

## Cobertura de casos

### A. Generación de código
- ✅ Código vacío rechazado
- ✅ Código solo espacios rechazado
- ✅ Payload vacío rechazado
- ✅ Código válido aceptado
- ✅ Estructura de payloads (compile, upload, Agent)

### B. Compilación
- ✅ Código vacío → 400, NO llama a arduino-cli
- ✅ Código válido no rechazado por NO_CODE
- ✅ Error del backend propagado correctamente

### C. Subida (precondiciones)
- ✅ FAIL si no hay código (NO_CODE)
- ✅ FAIL si no hay puerto (NO_PORT)
- ✅ PASS cuando code, port, board presentes (con mocks)

### D. Agent mock
- ✅ /health OK (con mock de cores)
- ✅ /compile código vacío → error
- ✅ /compile sketch.code vacío → error
- ✅ /compile sin code/files → error
- ✅ /compile OK con código válido (mock subprocess)

### E. Integración
- ✅ Compilación exitosa (payload válido)
- ✅ Upload listo (precondiciones OK)
- ✅ Código vacío → error controlado, no llama compile real
- ✅ Error de backend propagado sin explosión

## Comandos para ejecutar

### Tests Django (editor)
```bash
python manage.py test editor.tests.test_ide_code_generation
python manage.py test editor.tests.test_ide_compile_flow
python manage.py test editor.tests.test_ide_upload_preconditions
python manage.py test editor.tests.test_ide_integration
```

Todos a la vez:
```bash
python manage.py test editor.tests.test_ide_code_generation editor.tests.test_ide_compile_flow editor.tests.test_ide_upload_preconditions editor.tests.test_ide_integration -v 2
```

### Tests del Agent
```bash
pip install -r agent/requirements.txt
python -m unittest agent.tests.test_agent_compile_mock -v
```

## Helpers extraídos

Módulo `editor/ide_validation.py` con funciones puras:
- `validate_compile_payload(data)` → (valid, error_code, error_message)
- `validate_upload_payload(data)` → (valid, error_code, error_message)
- `build_compile_payload(code, fqbn)`
- `build_upload_payload(code, port, fqbn)`
- `build_agent_compile_payload(code, fqbn)`

## Bugs detectados por estos tests

1. **Código vacío con bloques** – El frontend ahora usa `getCodeForCompile()` que fuerza regeneración y valida antes de enviar.
2. **Payload vacío vs dict vacío** – `validate_compile_payload` diferencia `None` (NO_PAYLOAD) de `{}` (NO_CODE).
3. **Agent /health Unicode** – En Windows, `get_cores_status` puede fallar por caracteres; los tests mockean `get_cores_status`.

## Restricciones cumplidas

- ❌ No modo diagnóstico visual
- ❌ No cambios al diseño del IDE
- ❌ No cambios al flujo funcional (solo helpers opcionales)
- ✅ Tests detectan bugs reales
- ✅ No dependen de hardware real
