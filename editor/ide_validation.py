"""
Helpers de validación para el flujo del IDE.
Funciones puras y testeables para precondiciones de compilación y subida.

No modifican el flujo actual del IDE. Sirven para:
- Tests automáticos
- Posible reutilización en vistas
"""
from typing import Tuple, Optional, Dict, Any


def validate_compile_payload(data: dict) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valida el payload para compilación.
    
    Returns:
        (valid, error_code, error_message)
    """
    if data is None:
        return False, 'NO_PAYLOAD', 'No se proporcionó payload'
    
    code = data.get('code', '') or data.get('sketch_ino_text', '') or ''
    sketch = data.get('sketch') or {}
    code_from_sketch = sketch.get('code', '') if isinstance(sketch, dict) else ''
    
    code = str(code or code_from_sketch).strip()
    
    if not code:
        return False, 'NO_CODE', 'No hay código para compilar'
    
    return True, None, None


def validate_upload_payload(data: dict) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valida el payload para subida (upload).
    
    Returns:
        (valid, error_code, error_message)
    """
    if data is None:
        return False, 'NO_PAYLOAD', 'No se proporcionó payload'
    
    code = data.get('code', '') or ''
    code = str(code).strip()
    
    if not code:
        return False, 'NO_CODE', 'No hay código para subir'
    
    port = data.get('port', '') or ''
    port = str(port).strip()
    
    if not port:
        return False, 'NO_PORT', 'No se especificó puerto'
    
    return True, None, None


def build_compile_payload(code: str, fqbn: str = 'arduino:avr:uno') -> dict:
    """Construye el payload esperado para /api/compile/ o Agent /compile."""
    return {
        'code': code,
        'fqbn': fqbn,
    }


def build_upload_payload(code: str, port: str, fqbn: str = 'arduino:avr:uno') -> dict:
    """Construye el payload esperado para /api/upload/ o Agent /upload."""
    return {
        'code': code,
        'port': port,
        'board': fqbn,
        'fqbn': fqbn,
    }


def build_agent_compile_payload(code: str, fqbn: str = 'arduino:avr:uno') -> dict:
    """Construye el payload que el frontend envía al Agent (/compile)."""
    return {
        'fqbn': fqbn,
        'sketch': {'code': code},
        'return_job_id': True,
    }
