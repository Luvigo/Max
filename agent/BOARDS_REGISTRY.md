# Board Registry

**Fuente única:** `agent/boards_registry.json`

Formato: `[{ "label", "fqbn", "family": "avr"|"esp32", "notes" }]`

- **Agent:** Lee este archivo y sirve `GET /boards`
- **IDE:** Obtiene de Agent `/boards` → fallback `/static/editor/json/boards.json` → fallback embebido en `app.js`
- **Sincronización:** `agent/build_package.sh` copia a `editor/static/editor/json/boards.json` al empaquetar

Para añadir placas: editar solo `boards_registry.json` y ejecutar `bash agent/build_package.sh`.
