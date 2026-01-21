# Módulo 5: Agent Local Institucional

## Descripción

Este módulo convierte el Agent Local en un componente institucional serio con monitoreo, control y UX clara. **NO modifica la lógica de compilación ni subida del Agent existente**.

## Objetivo

1. Saber qué Agents existen
2. A qué institución pertenecen
3. Si están online/offline
4. Qué versión usan
5. Mostrar su estado en el IDE
6. Dar herramientas de diagnóstico y soporte

## Componentes

### Modelo

- **AgentInstance**: Instancia de Agent Local registrada con:
  - institution (FK)
  - hostname, os, agent_version
  - status (ONLINE | OFFLINE | ERROR)
  - last_seen, meta (JSON)

### APIs (solo control, no ejecución)

- `POST /api/agent/register/`: Registrar Agent
- `POST /api/agent/heartbeat/`: Enviar heartbeat periódico
- `GET /api/agent/list/`: Listar Agents
- `GET /api/agent/<id>/`: Estado de un Agent
- `GET /api/agent/check/`: Verificar Agent desde IDE

### Vistas

#### Admin
- Lista global de Agents
- Detalle de Agent
- Estadísticas (online/offline/error)

#### Institución
- Lista de Agents propios
- Detalle de Agent
- Diagnóstico básico

### Integración en IDE

- Banner dinámico de estado del Agent
- Botón "Verificar conexión"
- Botón "Guía instalación"
- NO permite subir si Agent está OFFLINE

## Seguridad

- Token institucional para registro
- Cross-tenant protection: Institución solo ve sus Agents
- Verificación periódica de estado basada en last_seen

## Reglas

- El Agent se registra una sola vez (unique: institution + hostname)
- Luego envía heartbeat cada X segundos
- Si last_seen > 2 minutos → OFFLINE automático
- Admin ve todos los Agents
- Institución ve solo los suyos

## Restricciones

❌ NO modificar:
- Lógica de compilación
- Lógica de subida
- Protocolo serial

✅ SOLO:
- Monitoreo
- Control
- UX
- Estructura institucional

## Diagramas UML

- `use_cases.puml`: Casos de uso del módulo
- `class_diagram.puml`: Diagrama de clases
