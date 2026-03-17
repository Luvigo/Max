#!/usr/bin/env python3
"""
MAX-IDE Agent Local
Agente que corre en el PC del usuario para compilar y subir código a Arduino.

Uso:
    python agent.py [--port 8765] [--arduino-cli /path/to/arduino-cli]

Endpoints:
    GET  /health   - Estado del agent
    GET  /ports    - Lista de puertos seriales
    POST /compile  - Compilar código (sin subir)
    POST /upload   - Compilar y subir código al Arduino
"""

import os
import sys
import json
import time
import shutil
import tempfile
import platform
import argparse
import subprocess
import hashlib
import base64
import uuid
from pathlib import Path
from datetime import datetime

# Job store para upload por job_id (compile -> upload sin reenviar artifacts)
_upload_job_store = {}
JOB_TTL_SEC = 600  # 10 min


def _store_upload_job(build_dir, family, fqbn):
    """Guarda un job de compilación. Retorna job_id."""
    job_id = str(uuid.uuid4())[:12]
    _upload_job_store[job_id] = {
        'build_dir': build_dir,
        'family': family,
        'fqbn': fqbn,
        'created_at': time.time(),
    }
    return job_id


def _get_upload_job(job_id):
    """Obtiene un job. Retorna dict o None si no existe/expirado."""
    job = _upload_job_store.get(job_id)
    if not job:
        return None
    if time.time() - job['created_at'] > JOB_TTL_SEC:
        del _upload_job_store[job_id]
        return None
    if not os.path.isdir(job['build_dir']):
        del _upload_job_store[job_id]
        return None
    return job


try:
    from flask import Flask, request, jsonify, make_response
    from flask_cors import CORS
except ImportError:
    print("ERROR: Faltan dependencias. Instala con:")
    print("  pip install flask flask-cors requests")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: Falta 'requests'. Instala con:")
    print("  pip install requests")
    sys.exit(1)

try:
    import serial.tools.list_ports
except ImportError:
    print("ERROR: Falta 'pyserial'. Instala con:")
    print("  pip install pyserial")
    sys.exit(1)

# ============================================
# CONFIGURACIÓN
# ============================================

VERSION = "1.2.0"
DEFAULT_PORT = 8765

# ============================================
# FUNCIONES DE UTILIDAD - PUERTO SERIAL
# ============================================

def reset_serial_port(port, log_func=None):
    """
    Intenta limpiar/resetear un puerto serial antes de usarlo.
    Esto puede ayudar si el puerto quedó "bloqueado" por una conexión anterior.
    
    Args:
        port: Nombre del puerto (ej: "COM3", "/dev/ttyUSB0")
        log_func: Función opcional para logging
    
    Returns:
        bool: True si se pudo limpiar, False si hubo error
    """
    import serial
    
    def log(msg):
        if log_func:
            log_func(msg)
        else:
            print(f"[RESET_PORT] {msg}")
    
    log(f"Intentando limpiar puerto {port}...")
    
    try:
        # Paso 1: Intentar cerrar cualquier conexión existente
        # abriendo y cerrando el puerto
        try:
            ser = serial.Serial()
            ser.port = port
            ser.baudrate = 9600
            ser.timeout = 0.5
            ser.dtr = False
            ser.rts = False
            
            # Abrir el puerto
            ser.open()
            log(f"Puerto {port} abierto para limpieza")
            
            # Limpiar buffers
            if ser.is_open:
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                log("Buffers limpiados")
            
            # Pequeña pausa
            time.sleep(0.2)
            
            # Cerrar
            ser.close()
            log(f"Puerto {port} cerrado correctamente")
            
        except serial.SerialException as e:
            # Si no se puede abrir, puede que ya esté cerrado o bloqueado
            log(f"No se pudo abrir para limpiar: {e}")
            # Continuar de todos modos
        
        # Paso 2: En Windows, intentar reset adicional
        if platform.system() == 'Windows':
            log("Aplicando reset adicional para Windows...")
            try:
                # Intentar con DTR toggle (reset del Arduino)
                ser = serial.Serial()
                ser.port = port
                ser.baudrate = 1200  # Baudrate especial para forzar reset en algunos Arduinos
                ser.timeout = 0.1
                ser.open()
                ser.dtr = True
                time.sleep(0.1)
                ser.dtr = False
                time.sleep(0.1)
                ser.close()
                log("Reset DTR aplicado")
            except Exception as e:
                log(f"Reset DTR falló (normal si el puerto ya está limpio): {e}")
        
        # Paso 3: Esperar un momento para que el puerto se estabilice
        log("Esperando estabilización del puerto...")
        time.sleep(0.5)
        
        log(f"✓ Puerto {port} listo")
        return True
        
    except Exception as e:
        log(f"Error durante limpieza de puerto: {e}")
        return False


def force_close_port_windows(port):
    """
    Intenta forzar el cierre de un puerto en Windows usando comandos del sistema.
    
    Args:
        port: Nombre del puerto (ej: "COM3")
    
    Returns:
        bool: True si se ejecutó el comando, False si falló
    """
    if platform.system() != 'Windows':
        return False
    
    try:
        # En Windows, mode puede ayudar a resetear el puerto
        subprocess.run(
            ['mode', port],
            capture_output=True,
            timeout=5
        )
        time.sleep(0.3)
        return True
    except Exception:
        return False

# Dominios permitidos para CORS
# El Agent corre localmente, así que permitimos todos los orígenes
# ya que solo es accesible desde localhost de todos modos
ALLOWED_ORIGINS = "*"  # Permitir todos los orígenes (el Agent solo es accesible localmente)

# Buscar arduino-cli en diferentes ubicaciones
def find_arduino_cli():
    """Busca arduino-cli en el sistema."""
    possible_paths = [
        # Linux/Mac
        "/usr/local/bin/arduino-cli",
        "/usr/bin/arduino-cli",
        os.path.expanduser("~/.local/bin/arduino-cli"),
        os.path.expanduser("~/bin/arduino-cli"),
        # Mismo directorio que el agent (Linux/Mac)
        os.path.join(os.path.dirname(__file__), "arduino-cli"),
        os.path.join(os.path.dirname(__file__), "..", "bin", "arduino-cli"),
        # Windows - mismo directorio que el agent
        os.path.join(os.path.dirname(__file__), "arduino-cli.exe"),
        # Windows - rutas comunes
        os.path.expanduser("~\\AppData\\Local\\Arduino15\\arduino-cli.exe"),
        os.path.expanduser("~\\AppData\\Local\\Programs\\arduino-cli\\arduino-cli.exe"),
        "C:\\Program Files\\Arduino CLI\\arduino-cli.exe",
        "C:\\Program Files (x86)\\Arduino CLI\\arduino-cli.exe",
    ]
    
    # Buscar en PATH
    which_result = shutil.which("arduino-cli")
    if which_result:
        return which_result
    
    # Buscar en rutas conocidas
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    return None

ARDUINO_CLI = find_arduino_cli()

# Cores requeridos por el board registry (AVR + ESP32)
REQUIRED_CORES = ['arduino:avr', 'esp32:esp32']


def ensure_cores_installed():
    """
    Verifica arduino-cli, versión y cores instalados (arduino:avr, esp32:esp32).
    Si falta alguno, intenta instalarlo. Idempotente.
    
    Returns:
        dict: {
            'arduino_cli_ok': bool,
            'arduino_cli_version': str|None,
            'cores': {'avr_ok': bool, 'esp32_ok': bool},
            'errors': [str, ...]
        }
    """
    result = {
        'arduino_cli_ok': False,
        'arduino_cli_version': None,
        'cores': {'avr_ok': False, 'esp32_ok': False},
        'errors': []
    }
    
    def log(msg):
        print(f"[CORES] {msg}")
    
    # 1) Verificar arduino-cli existe
    if not ARDUINO_CLI:
        result['errors'].append('arduino-cli no encontrado')
        log("✗ arduino-cli no encontrado")
        return result
    
    result['arduino_cli_ok'] = True
    log(f"arduino-cli: {ARDUINO_CLI}")
    
    # 2) Obtener versión
    try:
        r = subprocess.run(
            [ARDUINO_CLI, 'version'],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0:
            out = r.stdout.strip()
            if 'Version:' in out:
                result['arduino_cli_version'] = out.split('Version:')[1].split()[0].strip()
            elif out:
                result['arduino_cli_version'] = out.split()[0] if out else None
            log(f"Versión: {result['arduino_cli_version'] or '?'}")
        else:
            result['errors'].append('arduino-cli version falló')
            log("✗ No se pudo obtener versión de arduino-cli")
    except Exception as e:
        result['errors'].append(f'arduino-cli version: {e}')
        log(f"✗ Error ejecutando arduino-cli: {e}")
        return result
    
    # 3) Listar cores instalados
    installed_cores = []
    try:
        r = subprocess.run(
            [ARDUINO_CLI, 'core', 'list'],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode == 0:
            for line in r.stdout.strip().split('\n')[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 1:
                    # Columna 0 = ID (ej: arduino:avr, esp32:esp32)
                    installed_cores.append(parts[0])
        else:
            result['errors'].append('arduino-cli core list falló')
            log("✗ No se pudo listar cores")
    except Exception as e:
        result['errors'].append(f'core list: {e}')
        log(f"✗ Error listando cores: {e}")
        return result
    
    # 4) Verificar e instalar cada core (idempotente)
    core_map = {'arduino:avr': 'avr_ok', 'esp32:esp32': 'esp32_ok'}
    for core in REQUIRED_CORES:
        is_installed = any(c == core or c.startswith(core + ':') for c in installed_cores)
        
        if is_installed:
            result['cores'][core_map[core]] = True
            log(f"✓ {core} ya instalado")
        else:
            log(f"Instalando {core}...")
            try:
                subprocess.run(
                    [ARDUINO_CLI, 'core', 'update-index'],
                    capture_output=True, text=True, timeout=120
                )
                r = subprocess.run(
                    [ARDUINO_CLI, 'core', 'install', core],
                    capture_output=True, text=True, timeout=180
                )
                if r.returncode == 0:
                    result['cores'][core_map[core]] = True
                    log(f"✓ {core} instalado correctamente")
                else:
                    err = (r.stderr or r.stdout or '').strip()[:200]
                    result['errors'].append(f'Instalación {core} falló: {err}')
                    log(f"✗ Error instalando {core}: {err}")
            except subprocess.TimeoutExpired:
                result['errors'].append(f'Timeout instalando {core}')
                log(f"✗ Timeout instalando {core}")
            except Exception as e:
                result['errors'].append(f'{core}: {e}')
                log(f"✗ Error instalando {core}: {e}")
    
    return result


# Cache del último resultado de ensure_cores (para no bloquear /health)
_cached_cores_status = None
_cached_cores_ts = 0
CORES_CACHE_TTL = 60  # segundos


def get_cores_status():
    """Obtiene estado de cores (con cache corto para no bloquear /health)."""
    global _cached_cores_status, _cached_cores_ts
    now = time.time()
    if _cached_cores_status is not None and (now - _cached_cores_ts) < CORES_CACHE_TTL:
        return _cached_cores_status
    _cached_cores_status = ensure_cores_installed()
    _cached_cores_ts = now
    return _cached_cores_status


def _core_id_from_fqbn(fqbn):
    """Extrae el core ID (package:arch) de un FQBN. Ej: esp32:esp32:esp32 -> esp32:esp32."""
    if not fqbn or not isinstance(fqbn, str):
        return None
    parts = fqbn.split(':')
    if len(parts) >= 2:
        return f'{parts[0]}:{parts[1]}'
    return None


def ensure_core_for_fqbn(fqbn, log_func=None):
    """
    Asegura que el core necesario para el FQBN esté instalado.
    Solo instala el core específico (no toca arduino:avr si compilamos ESP32 y viceversa).
    
    Returns:
        (ok: bool, error_msg: str|None) - ok=True si el core está listo, error_msg si falló.
    """
    def log(msg):
        if log_func:
            log_func(msg)
        else:
            print(f"[CORES] {msg}")

    core_id = _core_id_from_fqbn(fqbn)
    if not core_id:
        return True, None  # FQBN sin core reconocible, continuar

    if not ARDUINO_CLI:
        return False, 'arduino-cli no encontrado'

    # Listar cores instalados
    try:
        r = subprocess.run(
            [ARDUINO_CLI, 'core', 'list'],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode != 0:
            return False, 'No se pudo listar cores'
        installed = []
        for line in r.stdout.strip().split('\n')[1:]:
            parts = line.split()
            if parts:
                installed.append(parts[0])
    except Exception as e:
        log(f"Error listando cores: {e}")
        return False, str(e)

    is_installed = any(c == core_id or c.startswith(core_id + ':') for c in installed)
    if is_installed:
        log(f"Core {core_id} ya instalado")
        return True, None

    log(f"Instalando core {core_id} para {fqbn}...")
    try:
        subprocess.run(
            [ARDUINO_CLI, 'core', 'update-index'],
            capture_output=True, text=True, timeout=120
        )
        r = subprocess.run(
            [ARDUINO_CLI, 'core', 'install', core_id],
            capture_output=True, text=True, timeout=180
        )
        if r.returncode == 0:
            log(f"✓ Core {core_id} instalado correctamente")
            return True, None
        err = (r.stderr or r.stdout or '').strip()[:300]
        return False, f'Error instalando core {core_id}: {err}'
    except subprocess.TimeoutExpired:
        return False, f'Timeout instalando core {core_id}'
    except Exception as e:
        return False, str(e)

# ============================================
# FLASK APP
# ============================================

app = Flask(__name__)

# Configurar CORS - Permitir todos los orígenes ya que el Agent solo es accesible localmente
# Esto es necesario porque el frontend puede venir de HTTPS (Render) o HTTP (local)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=False)

# ============================================
# MIDDLEWARE - Headers de seguridad y CORS
# ============================================

@app.after_request
def add_security_headers(response):
    """Añade headers de seguridad y CORS a todas las respuestas."""
    response.headers['X-MAX-IDE-Agent'] = '1'
    response.headers['X-Agent-Version'] = VERSION
    # CORS headers explícitos para máxima compatibilidad
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-MAX-IDE-Client, X-Requested-With, Accept, Origin'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Max-Age'] = '86400'  # Cache preflight por 24h
    return response

@app.before_request
def handle_preflight():
    """Maneja todas las peticiones OPTIONS (preflight) de forma centralizada."""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-MAX-IDE-Client, X-Requested-With, Accept, Origin'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Max-Age'] = '86400'
        return response, 200

# ============================================
# ENDPOINT: GET /health
# ============================================

@app.route('/health', methods=['GET', 'OPTIONS'])
def health():
    """
    Verifica el estado del Agent.
    
    Response:
        {
            "ok": true,
            "version": "1.0.0",
            "ts": 1234567890,
            "platform": "Linux-6.x-x86_64",
            "arduino_cli": "/usr/bin/arduino-cli",
            "arduino_cli_version": "0.35.0"
        }
    """
    # OPTIONS se maneja en before_request
    
    # Obtener versión de arduino-cli
    cli_version = None
    if ARDUINO_CLI:
        try:
            result = subprocess.run(
                [ARDUINO_CLI, 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Extraer versión del output
                output = result.stdout.strip()
                if 'Version:' in output:
                    cli_version = output.split('Version:')[1].split()[0].strip()
                elif output:
                    cli_version = output.split()[0] if output else None
        except Exception:
            pass
    
    # Estado de cores (arduino:avr, esp32:esp32)
    cores_status = get_cores_status()
    return jsonify({
        'ok': True,
        'version': VERSION,
        'ts': int(time.time()),
        'platform': platform.platform(),
        'arduino_cli': ARDUINO_CLI,
        'arduino_cli_version': cli_version or cores_status.get('arduino_cli_version'),
        'python_version': platform.python_version(),
        'arduino_cli_ok': cores_status.get('arduino_cli_ok', False),
        'cores': cores_status.get('cores', {'avr_ok': False, 'esp32_ok': False}),
        'errors': cores_status.get('errors', [])
    })

# ============================================
# HELPERS - Puertos seriales
# ============================================

def _get_suggested_family(vid, pid, manufacturer):
    """
    Heurística para sugerir familia de placa según VID/PID/manufacturer.
    Returns: {'avr_candidate': bool, 'esp32_candidate': bool} o None si no se puede inferir.
    """
    if vid is None and (manufacturer or '').strip() == '':
        return None
    mf = (manufacturer or '').lower()
    avr = False
    esp32 = False
    # Arduino LLC (0x2341), Arduino SRL (0x2A03), FTDI (0x0403) → típico AVR
    if vid in (0x2341, 0x2A03, 0x0403):
        avr = True
    if 'arduino' in mf or 'ftdi' in mf:
        avr = True
    # CP210x (0x10C4), CH340 (0x1A86) → muy usados en ESP32 DevKit
    if vid in (0x10C4, 0x1A86):
        esp32 = True
    if 'cp210' in mf or 'ch340' in mf or 'ch341' in mf or 'silicon labs' in mf or 'wch' in mf:
        esp32 = True
    if avr or esp32:
        return {'avr_candidate': avr, 'esp32_candidate': esp32}
    return None


def _build_port_info(port, log_func):
    """Construye dict de info de puerto, con campos nuevos y retrocompatibilidad."""
    def safe_attr(obj, attr, default=None):
        try:
            v = getattr(obj, attr, default)
            return v if v is not None else default
        except Exception as e:
            log_func(f"[PORTS] No se pudo leer {attr}: {e}")
            return default

    device = safe_attr(port, 'device', '')
    name = safe_attr(port, 'name', '')
    desc = safe_attr(port, 'description', '')
    vid = safe_attr(port, 'vid')
    pid = safe_attr(port, 'pid')
    serial_num = safe_attr(port, 'serial_number')
    manufacturer = safe_attr(port, 'manufacturer')
    product = safe_attr(port, 'product')
    hwid = safe_attr(port, 'hwid')

    # Campos existentes (contrato IDE)
    port_info = {
        'device': device,
        'address': device,  # alias para IDE (port.address)
        'name': name or 'USB Serial',
        'description': desc or 'USB Serial',
        'board_name': desc or name or 'USB Serial',  # alias para IDE
        'vid': vid,
        'pid': pid,
        'serial_number': serial_num,
        'manufacturer': manufacturer,
        'product': product,
        'hwid': hwid,
    }
    # Nuevos campos (path, label, serialNumber)
    port_info['path'] = device
    port_info['label'] = desc or name or device or 'USB Serial'
    port_info['serialNumber'] = serial_num

    # Tipo y friendly_name (existentes)
    if vid == 0x2341 or vid == 0x2A03:
        port_info['type'] = 'arduino_official'
        port_info['friendly_name'] = 'Arduino Original'
    elif vid == 0x1A86:
        port_info['type'] = 'ch340'
        port_info['friendly_name'] = 'Arduino (CH340)'
    elif vid == 0x0403:
        port_info['type'] = 'ftdi'
        port_info['friendly_name'] = 'Arduino (FTDI)'
    elif vid == 0x10C4:
        port_info['type'] = 'cp210x'
        port_info['friendly_name'] = 'Arduino (CP2102)'
    elif vid == 0x239A:
        port_info['type'] = 'adafruit'
        port_info['friendly_name'] = 'Adafruit'
    elif vid == 0x1B4F:
        port_info['type'] = 'sparkfun'
        port_info['friendly_name'] = 'SparkFun'
    else:
        port_info['type'] = 'generic'
        port_info['friendly_name'] = desc or name or 'USB Serial'

    # suggested_family heurística
    sf = _get_suggested_family(vid, pid, manufacturer)
    port_info['suggested_family'] = sf

    return port_info


# ============================================
# ENDPOINT: GET /ports
# ============================================

@app.route('/ports', methods=['GET', 'OPTIONS'])
def list_ports():
    """
    Lista los puertos seriales disponibles.
    Filtra solo puertos USB reales (excluir ttyS* virtuales).

    Campos por puerto (cuando se puedan leer):
    - path, label, vid, pid, manufacturer, serialNumber
    - suggested_family: { avr_candidate, esp32_candidate } o null
    - Contrato IDE: device, name, description, type, friendly_name, etc.
    """
    def log(msg):
        print(f"[PORTS] {msg}")

    ports = []
    all_ports = []

    try:
        for port in serial.tools.list_ports.comports():
            try:
                is_usb_port = (
                    getattr(port, 'vid', None) is not None or
                    'USB' in (getattr(port, 'hwid', None) or '') or
                    'usb' in (getattr(port, 'device', '') or '').lower() or
                    'ACM' in (getattr(port, 'device', '') or '')
                )
            except Exception as e:
                log(f"No se pudo evaluar si es USB para {getattr(port, 'device', '?')}: {e}")
                is_usb_port = True

            if platform.system() == 'Windows':
                is_usb_port = True

            try:
                all_ports.append({
                    'device': getattr(port, 'device', None),
                    'vid': getattr(port, 'vid', None),
                    'is_usb': is_usb_port
                })
            except Exception as e:
                log(f"No se pudieron leer metadatos básicos: {e}")

            if not is_usb_port:
                continue

            try:
                port_info = _build_port_info(port, log)
                ports.append(port_info)
            except Exception as e:
                log(f"No se pudo construir info para puerto {getattr(port, 'device', '?')}: {e}")

    except Exception as e:
        log(f"Error listando puertos: {e}")
        return jsonify({
            'ok': False,
            'error': f'Error listando puertos: {str(e)}',
            'ports': [],
            'os_name': platform.system(),
            'os_version': platform.release()
        }), 500

    return jsonify({
        'ok': True,
        'ports': ports,
        'count': len(ports),
        'total_scanned': len(all_ports),
        'os_name': platform.system(),
        'os_version': platform.release()
    })

# ============================================
# ENDPOINT: GET /boards
# ============================================

def _load_boards_registry():
    """Carga el registry de placas desde JSON. Fuente única: agent/boards_registry.json"""
    registry_path = Path(__file__).resolve().parent / 'boards_registry.json'
    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[BOARDS] Error cargando registry: {e}")
        return []


def _get_board_by_fqbn(fqbn):
    """Busca un board en el registry por FQBN. Retorna dict con family, label o None si no existe."""
    if not fqbn or not isinstance(fqbn, str):
        return None
    boards = _load_boards_registry()
    for b in boards:
        if b.get('fqbn') == fqbn:
            return b
    return None


def _compute_sha256(filepath):
    """Calcula SHA256 de un archivo. Retorna hex string o None si falla."""
    try:
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def _collect_artifacts(build_dir, family, include_base64=False, max_base64_bytes=5 * 1024 * 1024):
    """
    Recorre build_dir buscando artefactos según familia.
    AVR: .hex (firmware.hex o *.hex)
    ESP32: firmware.bin, bootloader.bin, partitions.bin
    Returns: [{name, type, path, sha256, size, content_base64?}]
    """
    artifacts = []
    build_path = Path(build_dir)
    if not build_path.exists():
        return artifacts

    # Patrones por familia
    if family == 'avr':
        patterns = ['**/*.hex']
        type_map = {'hex': 'firmware'}
    elif family == 'esp32':
        patterns = ['**/firmware.bin', '**/bootloader.bin', '**/partitions.bin', '**/*.bin']
        type_map = {
            'firmware.bin': 'firmware',
            'bootloader.bin': 'bootloader',
            'partitions.bin': 'partitions',
        }
    else:
        patterns = ['**/*.hex', '**/*.bin']
        type_map = {}

    seen_paths = set()
    for pattern in patterns:
        for fp in build_path.glob(pattern):
            if not fp.is_file() or str(fp) in seen_paths:
                continue
            seen_paths.add(str(fp))
            name = fp.name
            size = fp.stat().st_size
            sha = _compute_sha256(fp)
            art_type = type_map.get(name)
            if art_type is None:
                art_type = 'firmware' if name.endswith('.hex') else 'binary'

            art = {
                'name': name,
                'type': art_type,
                'path': str(fp),
                'sha256': sha,
                'size': size,
            }
            if include_base64 and size <= max_base64_bytes:
                try:
                    with open(fp, 'rb') as f:
                        art['content_base64'] = base64.b64encode(f.read()).decode('ascii')
                except Exception:
                    pass
            artifacts.append(art)

    # Ordenar: firmware primero, luego bootloader, partitions, resto
    order = {'firmware': 0, 'bootloader': 1, 'partitions': 2, 'binary': 3}
    artifacts.sort(key=lambda a: (order.get(a['type'], 4), a['name']))
    return artifacts


def _port_exists(port):
    """Verifica si el puerto existe en la lista de puertos disponibles."""
    if not port:
        return False
    try:
        port_str = str(port)
        for p in serial.tools.list_ports.comports():
            dev = getattr(p, 'device', None) or ''
            if dev == port_str:
                return True
            if platform.system() == 'Windows' and dev.lower() == port_str.lower():
                return True
        return False
    except Exception:
        return False


def _resolve_hex_for_upload(data, temp_dir, log_func):
    """
    Resuelve el archivo HEX para upload desde: artifact(s), hex_url, o code.
    Returns: (hex_file_path, error_msg) - error_msg es None si ok.
    """
    def log(msg):
        log_func(msg)

    # 1) artifact(s) - preferencia
    artifacts = data.get('artifact') or data.get('artifacts')
    if artifacts is not None:
        if not isinstance(artifacts, list):
            artifacts = [artifacts]
        for art in artifacts:
            if not isinstance(art, dict):
                continue
            # content_base64
            if art.get('content_base64'):
                try:
                    raw = base64.b64decode(art['content_base64'])
                    hex_path = os.path.join(temp_dir, art.get('name', 'firmware.hex'))
                    with open(hex_path, 'wb') as f:
                        f.write(raw)
                    if len(raw) > 0:
                        log(f"HEX desde artifact (base64): {len(raw)} bytes")
                        return (hex_path, None)
                except Exception as e:
                    log(f"Error decodificando artifact base64: {e}")
                    continue
            # path (local)
            if art.get('path') and os.path.isfile(art['path']):
                p = art['path']
                if p.lower().endswith('.hex'):
                    log(f"HEX desde artifact path: {p}")
                    return (p, None)
            # url
            if art.get('url'):
                try:
                    r = requests.get(art['url'], timeout=30, stream=True)
                    r.raise_for_status()
                    hex_path = os.path.join(temp_dir, art.get('name', 'firmware.hex'))
                    with open(hex_path, 'wb') as f:
                        for chunk in r.iter_content(8192):
                            if chunk:
                                f.write(chunk)
                    if os.path.getsize(hex_path) > 0:
                        log(f"HEX descargado desde artifact URL: {os.path.getsize(hex_path)} bytes")
                        return (hex_path, None)
                except Exception as e:
                    log(f"Error descargando artifact URL: {e}")
                    continue

    # 2) hex_url (retrocompat)
    hex_url = data.get('hex_url')
    if hex_url:
        try:
            r = requests.get(hex_url, timeout=30, stream=True)
            r.raise_for_status()
            hex_path = os.path.join(temp_dir, 'firmware.hex')
            total = 0
            with open(hex_path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
                        total += len(chunk)
            if total == 0:
                return (None, 'Archivo HEX vacío')
            log(f"HEX descargado desde hex_url: {total} bytes")
            return (hex_path, None)
        except requests.RequestException as e:
            return (None, f'Error descargando HEX: {str(e)}')

    # 3) code - compilar localmente (retrocompat)
    code = data.get('code', '')
    if code and code.strip():
        fqbn = data.get('fqbn', 'arduino:avr:uno')
        board = _get_board_by_fqbn(fqbn)
        if not board:
            return (None, f'FQBN "{fqbn}" no está en el registry')
        sketch_dir = os.path.join(temp_dir, 'sketch_upload')
        os.makedirs(sketch_dir)
        with open(os.path.join(sketch_dir, 'sketch_upload.ino'), 'w', encoding='utf-8') as f:
            f.write(code)
        build_dir = os.path.join(temp_dir, 'build')
        os.makedirs(build_dir)
        try:
            r = subprocess.run(
                [ARDUINO_CLI, 'compile', '--fqbn', fqbn, '--output-dir', build_dir, sketch_dir],
                capture_output=True, text=True, timeout=120
            )
            if r.returncode != 0:
                return (None, f'Error de compilación: {(r.stderr or r.stdout or "")[:500]}')
            for fname in os.listdir(build_dir):
                if fname.endswith('.hex'):
                    hex_path = os.path.join(build_dir, fname)
                    log(f"HEX compilado localmente: {hex_path}")
                    return (hex_path, None)
            return (None, 'No se generó archivo HEX')
        except subprocess.TimeoutExpired:
            return (None, 'Timeout de compilación')
        except Exception as e:
            return (None, str(e))

    return (None, 'Se requiere artifact(s), hex_url o code')


def _do_upload_avr(port, fqbn, hex_file, log_func):
    """
    Ejecuta upload AVR con arduino-cli.
    Returns: (ok: bool, error_code: str|None, hint: str|None)
    No deja el puerto abierto (arduino-cli cierra al terminar).
    """
    def log(msg):
        log_func(msg)

    log("Limpiando puerto antes de upload...")
    reset_serial_port(port, log)
    time.sleep(0.3)

    upload_cmd = [
        ARDUINO_CLI, 'upload',
        '-p', port,
        '--fqbn', fqbn,
        '--input-file', hex_file,
        '-v'
    ]
    MAX_RETRIES = 2
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            log(f"Reintento {attempt}/{MAX_RETRIES}...")
            time.sleep(1.5)
            reset_serial_port(port, log)
            time.sleep(0.5)
        log(f"Ejecutando: {' '.join(upload_cmd)}")
        try:
            r = subprocess.run(upload_cmd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return (False, 'TIMEOUT', 'Timeout durante el upload. Verifica la conexión.')

        if r.returncode == 0:
            log("✓ Upload exitoso")
            return (True, None, None)

        err = (r.stderr + r.stdout).lower()
        if any(x in err for x in ['busy', 'in use', 'resource busy', 'com-state', "can't open device"]):
            if attempt < MAX_RETRIES:
                continue
            if "can't open device" in err or 'not found' in err or 'no such file' in err:
                return (False, 'PORT_NOT_FOUND', 'Puerto no encontrado. Verifica que el Arduino esté conectado.')
            return (False, 'PORT_BUSY', 'El puerto está ocupado. Cierra Serial Monitor u otras apps.')
        if 'permission denied' in err or 'access denied' in err:
            if platform.system() == 'Linux':
                hint = 'Permiso denegado. Ejecuta: sudo usermod -a -G dialout $USER\nY cierra sesión y vuelve a entrar.'
                if ARDUINO_CLI and 'snap' in ARDUINO_CLI:
                    hint = 'arduino-cli (snap) no puede acceder a puertos. Instala arduino-cli sin snap.'
            else:
                hint = 'Permiso denegado. Ejecuta el Agent como administrador.'
            return (False, 'PERMISSION_DENIED', hint)
        if 'sync' in err or 'not in sync' in err or 'programmer is not responding' in err:
            hint = 'Error de sincronización con el bootloader. Si es Nano clon CH340, usa "Arduino Nano (Old Bootloader)".'
            return (False, 'SYNC_FAIL', hint)
        if 'timeout' in err or 'timed out' in err:
            return (False, 'TIMEOUT', 'Timeout. Verifica la conexión y reinicia el Arduino.')
        break

    return (False, 'UPLOAD_FAIL', (r.stderr or r.stdout or 'Error desconocido')[:500])


# ============================================
# ENDPOINT: POST /esp32/install
# ============================================

@app.route('/esp32/install', methods=['POST', 'OPTIONS'])
def install_esp32_core():
    """
    Instala el core ESP32 automáticamente (arduino-cli core install esp32:esp32).
    Un solo clic para estudiantes, sin abrir CMD.
    """
    logs = []

    def log(msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        entry = f"[{timestamp}] {msg}"
        logs.append(entry)
        print(f"[ESP32-INSTALL] {msg}")

    try:
        if not ARDUINO_CLI:
            return jsonify({'ok': False, 'error': 'arduino-cli no encontrado', 'logs': logs}), 500

        log('Instalando core esp32:esp32... (puede tardar 1-3 minutos)')
        result = subprocess.run(
            [ARDUINO_CLI, 'core', 'install', 'esp32:esp32'],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    log(line)
        if result.stderr:
            for line in result.stderr.strip().split('\n'):
                if line.strip():
                    log(line)

        if result.returncode == 0:
            log('✓ Core esp32:esp32 instalado correctamente')
            return jsonify({'ok': True, 'logs': logs, 'message': 'Core ESP32 instalado. Intenta verificar/subir de nuevo.'})
        return jsonify({
            'ok': False,
            'error': result.stderr or result.stdout or 'Error desconocido',
            'logs': logs
        }), 500
    except subprocess.TimeoutExpired:
        log('Tiempo de espera agotado')
        return jsonify({'ok': False, 'error': 'La instalación tardó demasiado (timeout 5 min)', 'logs': logs}), 500
    except Exception as e:
        log(f'Error: {e}')
        return jsonify({'ok': False, 'error': str(e), 'logs': logs}), 500


@app.route('/boards', methods=['GET', 'OPTIONS'])
def list_boards():
    """
    Lista las placas soportadas (board registry).
    Fuente: agent/boards_registry.json
    
    Response:
        {
            "ok": true,
            "boards": [
                {"label": "Arduino UNO", "fqbn": "arduino:avr:uno", "family": "avr", "notes": ""},
                ...
            ]
        }
    """
    boards = _load_boards_registry()
    return jsonify({
        'ok': True,
        'boards': boards
    })

# ============================================
# ENDPOINT: POST /compile
# ============================================

@app.route('/compile', methods=['POST', 'OPTIONS'])
def compile_code():
    """
    Compila código Arduino sin subirlo.
    
    Request body:
        { "fqbn", "sketch": { "code"? | "files"? }, "options"? }
        Retrocompat: { "code", "fqbn" } → sketch.code
    
    Response:
        {
            "ok": true/false,
            "fqbn": "...",
            "family": "avr" | "esp32",
            "artifacts": [{ "name", "type", "path", "sha256", "size" }],
            "compile_log": "...",
            "logs": [...], "size": N, "message": "..."  (retrocompat)
        }
    """
    logs = []
    temp_dir = None
    
    def log(msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {msg}"
        logs.append(log_entry)
        print(f"[COMPILE] {msg}")
    
    def err_resp(msg, status=400):
        return jsonify({'ok': False, 'error': msg, 'logs': logs}), status
    
    try:
        if not ARDUINO_CLI:
            return err_resp(
                'arduino-cli no encontrado. Instálalo desde https://arduino.github.io/arduino-cli/',
                500
            )
        
        data = request.get_json()
        if not data:
            return err_resp('JSON body requerido')
        
        # fqbn (requerido)
        fqbn = data.get('fqbn') or data.get('board') or 'arduino:avr:uno'
        
        # Validar fqbn contra registry
        board = _get_board_by_fqbn(fqbn)
        if not board:
            return err_resp(f'FQBN "{fqbn}" no está en el registry de placas soportadas')
        
        family = board.get('family', 'avr')

        # Asegurar que el core necesario esté instalado (esp32:esp32 o arduino:avr)
        core_ok, core_err = ensure_core_for_fqbn(fqbn, log)
        if not core_ok:
            hint_esp32 = ''
            if family == 'esp32':
                hint_esp32 = ' Para ESP32, ejecuta manualmente: arduino-cli core install esp32:esp32'
            return err_resp(
                f'Core no disponible: {core_err}.{hint_esp32}',
                400
            )
        
        # sketch: { code?, files? } o retrocompat: code en raíz
        sketch = data.get('sketch') or {}
        code = sketch.get('code') or data.get('code', '')
        files = sketch.get('files')
        
        if not code and not files:
            return err_resp('No hay código para compilar (sketch.code o sketch.files requerido)')
        
        # Directorio temporal aislado por request
        if ARDUINO_CLI and 'snap' in ARDUINO_CLI:
            home_tmp = os.path.join(os.path.expanduser('~'), 'snap', 'arduino-cli', 'common', 'maxide-tmp')
        else:
            home_tmp = os.path.join(os.path.expanduser('~'), '.maxide-agent', 'tmp')
        os.makedirs(home_tmp, exist_ok=True)
        temp_dir = tempfile.mkdtemp(prefix='compile_', dir=home_tmp)
        
        sketch_name = 'sketch_verify'
        sketch_dir = os.path.join(temp_dir, sketch_name)
        os.makedirs(sketch_dir)
        
        if files and isinstance(files, dict):
            for fname, content in files.items():
                if not fname or content is None:
                    continue
                fpath = os.path.join(sketch_dir, fname)
                os.makedirs(os.path.dirname(fpath) or '.', exist_ok=True)
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(str(content))
            log(f"Sketch creado desde {len(files)} archivo(s)")
        else:
            main_ino = f'{sketch_name}.ino'
            if files and isinstance(files, list):
                main_ino = next((f for f in files if f.endswith('.ino')), main_ino)
            with open(os.path.join(sketch_dir, main_ino), 'w', encoding='utf-8') as f:
                f.write(code if code else 'void setup() {} void loop() {}')
            log(f"Sketch creado: {len(code)} caracteres")
        
        build_dir = os.path.join(temp_dir, 'build')
        os.makedirs(build_dir)
        
        compile_cmd = [
            ARDUINO_CLI, 'compile',
            '--fqbn', fqbn,
            '--output-dir', build_dir,
            sketch_dir
        ]
        
        options = data.get('options') or {}
        if options.get('warnings') == 'all':
            compile_cmd.append('--warnings')
            compile_cmd.append('all')
        
        tag = '[ESP32]' if family == 'esp32' else '[AVR]'
        log(f"{tag} Compilando para {fqbn} (family={family})")
        
        compile_result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if compile_result.stdout:
            for line in compile_result.stdout.strip().split('\n'):
                if line.strip():
                    logs.append(f"[stdout] {line}")
        if compile_result.stderr:
            for line in compile_result.stderr.strip().split('\n'):
                if line.strip():
                    logs.append(f"[stderr] {line}")
        
        if compile_result.returncode != 0:
            error_msg = compile_result.stderr or compile_result.stdout or 'Error desconocido'
            log(f"Error de compilación (exit code: {compile_result.returncode})")
            # Mensajes específicos según familia
            hint = None
            if family == 'esp32':
                hint = 'ESP32: Verifica que el core esté instalado (arduino-cli core install esp32:esp32)'
                if 'platform' in error_msg.lower() or 'package' in error_msg.lower() or 'unknown' in error_msg.lower():
                    hint = 'ESP32: Instala el core con: arduino-cli core install esp32:esp32'
            elif family == 'avr':
                hint = 'AVR: Verifica sintaxis y que el sketch tenga setup() y loop()'
            return jsonify({
                'ok': False,
                'error': error_msg,
                'logs': logs,
                'exit_code': compile_result.returncode,
                'fqbn': fqbn,
                'family': family,
                'compile_log': '\n'.join(logs),
                'hint': hint
            }), 400
        
        # Detectar artefactos (AVR: .hex, ESP32: .bin)
        artifacts = _collect_artifacts(build_dir, family, include_base64=False)
        total_size = sum(a['size'] for a in artifacts)
        
        log(f"✓ Compilación exitosa ({total_size} bytes, {len(artifacts)} artefacto(s))")
        
        compile_log = '\n'.join(logs)
        resp_data = {
            'ok': True,
            'fqbn': fqbn,
            'family': family,
            'artifacts': artifacts,
            'compile_log': compile_log,
            'message': 'Compilación exitosa',
            'logs': logs,
            'size': total_size,
        }
        # return_job_id: guardar build_dir para upload posterior sin reenviar artifacts
        if data.get('return_job_id') or (data.get('options') or {}).get('return_job_id'):
            jobs_base = os.path.join(home_tmp, 'jobs')
            os.makedirs(jobs_base, exist_ok=True)
            job_id = _store_upload_job(build_dir, family, fqbn)
            job_dir = os.path.join(jobs_base, job_id)
            os.makedirs(job_dir, exist_ok=True)
            # Copiar todo el árbol de build (AVR: .hex; ESP32: .bin en posible subdir)
            for item in os.listdir(build_dir):
                src = os.path.join(build_dir, item)
                dst = os.path.join(job_dir, item)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                elif os.path.isdir(src):
                    shutil.copytree(src, dst)
            _upload_job_store[job_id]['build_dir'] = job_dir
            resp_data['job_id'] = job_id
        return jsonify(resp_data)
        
    except subprocess.TimeoutExpired:
        log("Timeout de compilación (120s)")
        return jsonify({
            'ok': False,
            'error': 'Timeout de compilación',
            'logs': logs,
            'hint': 'La compilación tardó más de 2 minutos.'
        }), 408
        
    except Exception as e:
        log(f"Error inesperado: {str(e)}")
        return jsonify({
            'ok': False,
            'error': str(e),
            'logs': logs
        }), 500
        
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"[COMPILE] Error limpiando temp: {e}")

# ============================================
# HELPERS - Upload
# ============================================

def _port_exists(port):
    """Verifica si el puerto existe en la lista de puertos disponibles."""
    if not port:
        return False
    port_str = str(port).strip()
    try:
        for p in serial.tools.list_ports.comports():
            dev = getattr(p, 'device', None) or ''
            if dev == port_str:
                return True
            if platform.system() == 'Windows' and dev.lower() == port_str.lower():
                return True
        return False
    except Exception:
        return False


def _resolve_hex_for_upload(data, temp_dir, log_func):
    """
    Resuelve el archivo HEX para upload desde: build_dir, artifact(s), hex_url, o code.
    Returns: (hex_file_path, error_msg) - error_msg es None si ok.
    """
    # 0) build_dir (desde job_id o explícito)
    build_dir = data.get('build_dir') or data.get('build_path')
    if build_dir and os.path.isdir(build_dir):
        for f in os.listdir(build_dir):
            if f.endswith('.hex'):
                hex_path = os.path.join(build_dir, f)
                log_func(f"Usando HEX desde build_dir: {hex_path}")
                return hex_path, None

    artifacts = data.get('artifact') or data.get('artifacts')
    if isinstance(artifacts, dict):
        artifacts = [artifacts]
    elif not isinstance(artifacts, list):
        artifacts = []

    # 1) artifact(s): path, content_base64, o url
    for art in artifacts:
        if isinstance(art, dict):
            if art.get('path') and os.path.isfile(art['path']) and art['path'].lower().endswith('.hex'):
                log_func(f"Usando artifact por path: {art['path']}")
                return art['path'], None
            if art.get('content_base64'):
                try:
                    hex_path = os.path.join(temp_dir, 'firmware.hex')
                    with open(hex_path, 'wb') as f:
                        f.write(base64.b64decode(art['content_base64']))
                    if os.path.getsize(hex_path) > 0:
                        log_func(f"Usando artifact desde base64 ({os.path.getsize(hex_path)} bytes)")
                        return hex_path, None
                except Exception as e:
                    log_func(f"Error decodificando artifact base64: {e}")
                    return None, f"Artifact base64 inválido: {e}"
            if art.get('url'):
                try:
                    resp = requests.get(art['url'], timeout=30, stream=True)
                    resp.raise_for_status()
                    hex_path = os.path.join(temp_dir, 'firmware.hex')
                    with open(hex_path, 'wb') as f:
                        for chunk in resp.iter_content(8192):
                            if chunk:
                                f.write(chunk)
                    if os.path.getsize(hex_path) > 0:
                        log_func(f"Usando artifact desde URL ({os.path.getsize(hex_path)} bytes)")
                        return hex_path, None
                except Exception as e:
                    log_func(f"Error descargando artifact URL: {e}")
                    return None, f"Error descargando artifact: {e}"

    # 2) hex_url (retrocompat)
    hex_url = data.get('hex_url')
    if hex_url:
        try:
            resp = requests.get(hex_url, timeout=30, stream=True)
            resp.raise_for_status()
            hex_path = os.path.join(temp_dir, 'firmware.hex')
            with open(hex_path, 'wb') as f:
                for chunk in resp.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            if os.path.getsize(hex_path) > 0:
                log_func(f"HEX descargado desde URL ({os.path.getsize(hex_path)} bytes)")
                return hex_path, None
            return None, "Archivo HEX vacío"
        except Exception as e:
            return None, f"Error descargando HEX: {e}"

    # 3) code (compilar localmente)
    code = data.get('code')
    if code and code.strip():
        sketch_dir = os.path.join(temp_dir, 'sketch_upload')
        os.makedirs(sketch_dir)
        with open(os.path.join(sketch_dir, 'sketch_upload.ino'), 'w', encoding='utf-8') as f:
            f.write(code)
        build_dir = os.path.join(temp_dir, 'build')
        os.makedirs(build_dir)
        r = subprocess.run(
            [ARDUINO_CLI, 'compile', '--fqbn', data.get('fqbn', 'arduino:avr:uno'),
             '--output-dir', build_dir, sketch_dir],
            capture_output=True, text=True, timeout=120
        )
        if r.returncode != 0:
            return None, (r.stderr or r.stdout or 'Error de compilación')[:500]
        for f in os.listdir(build_dir):
            if f.endswith('.hex'):
                return os.path.join(build_dir, f), None
        return None, "No se generó archivo HEX"

    return None, "Se requiere artifact(s), hex_url o code"


def _do_upload_avr(port, fqbn, hex_file, log_func):
    """
    Ejecuta upload AVR con arduino-cli upload -p <port> --fqbn <fqbn> --input-file <hex>.
    Returns: (ok: bool, error_code: str|None, hint: str|None)
    """
    log_func("Limpiando puerto serial antes de upload...")
    reset_serial_port(port, log_func)
    time.sleep(0.3)

    upload_cmd = [ARDUINO_CLI, 'upload', '-p', port, '--fqbn', fqbn, '--input-file', hex_file, '-v']
    MAX_RETRIES = 2
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            log_func(f"Reintento {attempt}/{MAX_RETRIES}...")
            time.sleep(1.5)
            reset_serial_port(port, log_func)
            time.sleep(0.5)
        log_func(f"Ejecutando: {' '.join(upload_cmd)}")
        try:
            r = subprocess.run(upload_cmd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return False, 'TIMEOUT', 'Timeout durante el upload. Verifica la conexión y reinicia el Arduino.'
        if r.returncode == 0:
            return True, None, None
        err = (r.stderr + r.stdout).lower()
        if any(x in err for x in ['busy', 'in use', 'resource busy', 'com-state', 'timeout', "can't open device"]) and attempt < MAX_RETRIES:
            continue
        break

    out = r.stderr + r.stdout
    err_lower = out.lower()
    if "can't set com-state" in err_lower or 'com-state' in err_lower:
        return False, 'COM_STATE_ERROR', 'Error de comunicación con el puerto. Desconecta/reconecta el cable.'
    if 'busy' in err_lower or 'in use' in err_lower:
        return False, 'PORT_BUSY', 'Puerto ocupado. Cierra Serial Monitor u otras apps.'
    if 'sync' in err_lower or 'not in sync' in err_lower or 'programmer is not responding' in err_lower:
        return False, 'SYNC_FAIL', 'Error de sincronización con el bootloader. Si es Nano clon CH340, usa "Arduino Nano (Old Bootloader)".'
    if 'no such file' in err_lower or 'not found' in err_lower or "can't open device" in err_lower:
        return False, 'PORT_NOT_FOUND', 'Puerto no encontrado. Verifica conexión y cable.'
    if 'permission denied' in err_lower or 'access denied' in err_lower:
        hint = 'Permiso denegado. Linux: sudo usermod -a -G dialout $USER'
        if platform.system() == 'Linux' and ARDUINO_CLI and 'snap' in ARDUINO_CLI:
            hint = 'arduino-cli (snap) no accede a puertos. Instala arduino-cli sin snap.'
        return False, 'PERMISSION_DENIED', hint
    if 'timeout' in err_lower:
        return False, 'TIMEOUT', 'Timeout. Verifica conexión.'
    return False, 'UPLOAD_FAIL', out[:500]


# ============================================
# HELPERS - Upload ESP32
# ============================================

def _find_esptool():
    """Busca esptool en el sistema. Retorna path o None."""
    for name in ['esptool', 'esptool.py']:
        p = shutil.which(name)
        if p:
            return p
    for path in [
        os.path.join(os.path.expanduser('~'), '.local', 'bin', 'esptool.py'),
        '/usr/local/bin/esptool.py',
        '/usr/bin/esptool.py',
    ]:
        if os.path.isfile(path):
            return path
    try:
        import esptool
        return sys.executable + ' -m esptool'
    except ImportError:
        pass
    return None


def _esp32_reset_for_bootloader(port, log_func):
    """
    Intenta poner ESP32 en modo bootloader via DTR/RTS.
    Returns: True si se pudo, False si no (mostrar hint manual).
    """
    import serial
    try:
        ser = serial.Serial(port=port, baudrate=115200, timeout=0.1)
        try:
            ser.dtr = False
            ser.rts = True
            time.sleep(0.1)
            ser.rts = False
            time.sleep(0.05)
            ser.dtr = True
            time.sleep(0.05)
            ser.dtr = False
            log_func("DTR/RTS toggled para modo bootloader")
            return True
        finally:
            ser.close()
    except Exception as e:
        log_func(f"No se pudo toggle DTR/RTS: {e}")
        return False


def _resolve_bin_for_upload_esp32(data, temp_dir, log_func):
    """
    Resuelve build_dir o artefactos .bin para ESP32.
    Returns: (build_dir_path, error_msg) - build_dir contiene firmware.bin, etc.
    """
    # 1) build_dir explícito (incl. job_id -> build_dir)
    build_dir = data.get('build_dir') or data.get('build_path')
    if build_dir and os.path.isdir(build_dir):
        if any(Path(build_dir).rglob('*.bin')):
            log_func(f"Usando build_dir: {build_dir}")
            return build_dir, None
        return None, f"build_dir {build_dir} no contiene archivos .bin"

    # 2) artifact(s) con firmware.bin
    artifacts = data.get('artifact') or data.get('artifacts')
    if isinstance(artifacts, dict):
        artifacts = [artifacts]
    elif not isinstance(artifacts, list):
        artifacts = []

    esp32_bin_dir = os.path.join(temp_dir, 'esp32_bin')
    os.makedirs(esp32_bin_dir, exist_ok=True)
    has_firmware = False

    for art in artifacts:
        if not isinstance(art, dict):
            continue
        name = art.get('name', '')
        if not name.endswith('.bin'):
            continue
        out_path = os.path.join(esp32_bin_dir, name)
        if art.get('path') and os.path.isfile(art['path']):
            shutil.copy2(art['path'], out_path)
            if 'firmware' in name.lower():
                has_firmware = True
            log_func(f"Artifact {name} desde path")
        elif art.get('content_base64'):
            try:
                with open(out_path, 'wb') as f:
                    f.write(base64.b64decode(art['content_base64']))
                if 'firmware' in name.lower():
                    has_firmware = True
                log_func(f"Artifact {name} desde base64")
            except Exception as e:
                log_func(f"Error artifact {name}: {e}")
        elif art.get('url'):
            try:
                resp = requests.get(art['url'], timeout=30, stream=True)
                resp.raise_for_status()
                with open(out_path, 'wb') as f:
                    for chunk in resp.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                if os.path.getsize(out_path) > 0 and 'firmware' in name.lower():
                    has_firmware = True
                log_func(f"Artifact {name} desde URL")
            except Exception as e:
                log_func(f"Error descargando {name}: {e}")

    if has_firmware:
        return esp32_bin_dir, None

    # 3) code - compilar
    code = data.get('code')
    if code and code.strip():
        fqbn = data.get('fqbn', 'esp32:esp32:esp32')
        sketch_dir = os.path.join(temp_dir, 'sketch_esp32')
        os.makedirs(sketch_dir)
        with open(os.path.join(sketch_dir, 'sketch_esp32.ino'), 'w', encoding='utf-8') as f:
            f.write(code)
        build_dir = os.path.join(temp_dir, 'build_esp32')
        os.makedirs(build_dir)
        try:
            r = subprocess.run(
                [ARDUINO_CLI, 'compile', '--fqbn', fqbn, '--output-dir', build_dir, sketch_dir],
                capture_output=True, text=True, timeout=120
            )
            if r.returncode != 0:
                return None, (r.stderr or r.stdout or 'Error de compilación')[:500]
            if any(f.endswith('.bin') for f in os.listdir(build_dir)):
                log_func("Compilación ESP32 exitosa")
                return build_dir, None
            return None, "No se generaron archivos .bin"
        except subprocess.TimeoutExpired:
            return None, "Timeout de compilación"
        except Exception as e:
            return None, str(e)

    return None, "Se requiere build_dir, artifact(s) con firmware.bin, o code"


def _do_upload_esp32(port, fqbn, build_dir, log_func):
    """
    Upload ESP32. Estrategia 1: arduino-cli. Estrategia 2: esptool.
    Returns: (ok, strategy_used, error_code, hint, hints_list)
    """
    hints = []
    hints.append("Drivers: CH340/CP2102 suelen necesitar instalación. Linux: udev rules o sudo usermod -a -G dialout $USER.")
    hints.append("CH340: Windows/Mac instalar desde wch.cn. Linux: a veces funciona con dialout.")
    hints.append("CP2102: Silicon Labs driver. Suele funcionar out-of-box en Mac.")
    hints.append("Si falla: mantén BOOT, presiona EN (reset), suelta EN, luego suelta BOOT.")

    t0 = time.time()
    log_func("Preparando upload ESP32...")

    # Reset para bootloader
    if _esp32_reset_for_bootloader(port, log_func):
        time.sleep(0.3)
    else:
        hints.insert(0, "Mantén BOOT y presiona EN para entrar en modo bootloader, luego reintenta.")

    # Estrategia 1: arduino-cli (con reintento tras fallo timeout/bootloader)
    upload_cmd = [
        ARDUINO_CLI, 'upload',
        '-p', port,
        '--fqbn', fqbn,
        '--input-dir', build_dir,
        '-v'
    ]
    err_out = ''
    for attempt in range(2):
        if attempt > 0:
            log_func("Reintento con reset a modo bootloader...")
            if _esp32_reset_for_bootloader(port, log_func):
                time.sleep(0.5)
        log_func(f"Estrategia 1: arduino-cli upload (intento {attempt + 1}/2)...")
        t1 = time.time()
        try:
            r = subprocess.run(upload_cmd, capture_output=True, text=True, timeout=120)
            elapsed = time.time() - t1
            log_func(f"arduino-cli upload: {elapsed:.1f}s, exit={r.returncode}")
            if r.returncode == 0:
                log_func(f"✓ Upload ESP32 exitoso (arduino-cli) en {time.time()-t0:.1f}s")
                return True, 'arduino-cli', None, None, hints
            err_out = r.stderr + r.stdout
            log_func(f"arduino-cli falló: {err_out[:300]}")
            # Reintentar solo si parece timeout/bootloader
            if 'timed out' in err_out.lower() or 'timeout' in err_out.lower() or 'connecting' in err_out.lower():
                continue
            break
        except subprocess.TimeoutExpired:
            log_func("arduino-cli timeout")
            err_out = 'Timeout'
            if attempt == 0:
                continue
            return False, 'arduino-cli', 'TIMEOUT', 'ESP32: Timeout. Mantén BOOT pulsado y presiona EN.', hints
        except FileNotFoundError:
            log_func("arduino-cli no encontrado")
            return False, None, 'ARDUINO_CLI_MISSING', 'arduino-cli no encontrado', hints
        except Exception as e:
            log_func(f"arduino-cli error: {e}")
            err_out = str(e)
        break

    # Estrategia 2: esptool (fallback cuando arduino-cli falla)
    # Reintentar reset bootloader antes de esptool
    log_func("arduino-cli falló. Reintentando modo bootloader para esptool...")
    if _esp32_reset_for_bootloader(port, log_func):
        time.sleep(0.5)

    esptool_path = _find_esptool()
    if not esptool_path:
        return False, 'arduino-cli', 'UPLOAD_FAIL', 'arduino-cli falló y esptool no está instalado. pip install esptool', hints

    log_func("Estrategia 2: esptool write_flash...")
    t2 = time.time()
    build_path = Path(build_dir)
    exclude = {'bootloader.bin', 'partitions.bin'}
    firmware = None
    for fp in build_path.rglob('*.bin'):
        if fp.name.lower() not in exclude and fp.is_file():
            firmware = fp
            break
    if not firmware:
        firmware = build_path / 'firmware.bin'
    if not firmware or not firmware.is_file():
        return False, 'arduino-cli', 'UPLOAD_FAIL', 'No se encontró firmware.bin', hints

    # Direcciones típicas ESP32 Arduino: 0x1000 bootloader, 0x8000 partitions, 0x10000 firmware
    bootloader = build_path / 'bootloader.bin'
    partitions = build_path / 'partitions.bin'
    flash_args = []
    if bootloader.is_file():
        flash_args.extend(['0x1000', str(bootloader)])
    if partitions.is_file():
        flash_args.extend(['0x8000', str(partitions)])
    flash_args.extend(['0x10000', str(firmware)])

    if esptool_path.startswith(sys.executable) or ' -m ' in esptool_path:
        cmd = esptool_path.split() + ['--port', port, 'write_flash'] + flash_args
    else:
        cmd = [esptool_path, '--port', port, 'write_flash'] + flash_args

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        elapsed = time.time() - t2
        log_func(f"esptool write_flash: {elapsed:.1f}s, exit={r.returncode}")
        if r.returncode == 0:
            log_func(f"✓ Upload exitoso (esptool) en {time.time()-t0:.1f}s")
            return True, 'esptool', None, None, hints
        err_out = r.stderr + r.stdout
        log_func(f"esptool falló: {err_out[:300]}")
    except subprocess.TimeoutExpired:
        return False, 'esptool', 'TIMEOUT', 'Timeout esptool.', hints
    except Exception as e:
        err_out = str(e)
        log_func(f"esptool error: {e}")

    err_lower = err_out.lower()
    if 'permission denied' in err_lower or 'access denied' in err_lower:
        return False, 'esptool', 'PERMISSION_DENIED', 'Permiso denegado. Linux: sudo usermod -a -G dialout $USER', hints
    if 'no such file' in err_lower or 'not found' in err_lower or "can't open" in err_lower:
        return False, 'esptool', 'PORT_NOT_FOUND', 'Puerto no encontrado.', hints
    if 'timed out' in err_lower or 'timeout' in err_lower:
        return False, 'esptool', 'TIMEOUT', 'Timeout. Mantén BOOT y presiona EN antes de subir.', hints

    return False, 'esptool', 'UPLOAD_FAIL', (err_out[:500] if isinstance(err_out, str) else str(err_out)[:500]), hints


# ============================================
# ENDPOINT: POST /upload
# ============================================

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload():
    """
    Sube firmware al Arduino. Endpoint único que rutea por family (avr/esp32).
    
    Request: { fqbn, port, artifacts? | job_id? }
    - artifacts: [{ path?, content_base64?, url?, name? }] o artifact: {...}
    - job_id: ID de compilación previa (compile con return_job_id=true)
    - Deprecado pero soportado: hex_url, code (compilar y subir)
    
    Response unificada: { ok, port, fqbn, family, upload_log, logs?, ... }
    """
    logs = []
    temp_dir = None

    def log(msg):
        ts = datetime.now().strftime('%H:%M:%S')
        logs.append(f"[{ts}] {msg}")
        print(f"[UPLOAD] {msg}")

    def err(code, msg, hint=None):
        return jsonify({
            'ok': False, 'port': data.get('port'), 'fqbn': data.get('fqbn'),
            'family': family, 'upload_log': '\n'.join(logs), 'logs': logs,
            'error': msg, 'error_code': code, 'hint': hint
        }), 400 if code in ('PORT_NOT_FOUND', 'PERMISSION_DENIED', 'INVALID_FQBN') else 500

    try:
        if not ARDUINO_CLI:
            return jsonify({
                'ok': False, 'error': 'arduino-cli no encontrado',
                'logs': logs, 'hint': 'https://arduino.github.io/arduino-cli/'
            }), 500

        data = request.get_json()
        if not data:
            return jsonify({'ok': False, 'error': 'JSON body requerido', 'logs': logs}), 400

        port = data.get('port')
        fqbn = data.get('fqbn', 'arduino:avr:uno')

        if not port:
            return jsonify({'ok': False, 'error': 'Parámetro "port" requerido', 'logs': logs}), 400

        board = _get_board_by_fqbn(fqbn)
        if not board:
            return jsonify({
                'ok': False, 'error': f'FQBN "{fqbn}" no está en el registry',
                'logs': logs, 'error_code': 'INVALID_FQBN'
            }), 400
        family = board.get('family', 'avr')

        if not _port_exists(port):
            log(f"Puerto {port} no encontrado en la lista de puertos")
            return err('PORT_NOT_FOUND', f'Puerto "{port}" no existe o no está disponible', 'Verifica que el dispositivo esté conectado.')

        tag = '[ESP32]' if family == 'esp32' else '[AVR]'
        log(f"{tag} Iniciando upload a {port} con {fqbn} (family={family})")

        # Resolver job_id si se proporciona (artifacts desde compile previo)
        job_id = data.get('job_id')
        if job_id:
            job = _get_upload_job(job_id)
            if job:
                data = dict(data)
                data['build_dir'] = job.get('build_dir') or data.get('build_dir')
                if job.get('fqbn'):
                    data['fqbn'] = job['fqbn']
                    fqbn = job['fqbn']
                    board = _get_board_by_fqbn(fqbn)
                    if board:
                        family = board.get('family', 'avr')
                log(f"Usando job_id {job_id} (build_dir, family={family})")
            else:
                return jsonify({
                    'ok': False, 'error': f'job_id "{job_id}" no encontrado o expirado',
                    'logs': logs, 'port': port, 'fqbn': fqbn, 'family': family,
                    'upload_log': '\n'.join(logs), 'error_code': 'JOB_NOT_FOUND'
                }), 400

        # Asegurar que el core esté instalado (tras resolver job_id, tenemos fqbn final)
        core_ok, core_err = ensure_core_for_fqbn(fqbn, log)
        if not core_ok:
            hint = ' Para ESP32: arduino-cli core install esp32:esp32' if family == 'esp32' else ''
            return jsonify({
                'ok': False, 'error': f'Core no disponible: {core_err}.{hint}',
                'logs': logs, 'error_code': 'CORE_NOT_INSTALLED', 'family': family,
                'upload_log': '\n'.join(logs)
            }), 400

        home_tmp = os.path.join(os.path.expanduser('~'), 'snap', 'arduino-cli', 'common', 'maxide-tmp') if (ARDUINO_CLI and 'snap' in ARDUINO_CLI) else os.path.join(os.path.expanduser('~'), '.maxide-agent', 'tmp')
        os.makedirs(home_tmp, exist_ok=True)
        temp_dir = tempfile.mkdtemp(prefix='upload_', dir=home_tmp)

        if family == 'avr':
            hex_file, resolve_err = _resolve_hex_for_upload(data, temp_dir, log)
            if resolve_err:
                return jsonify({
                    'ok': False, 'error': resolve_err, 'logs': logs,
                    'port': port, 'fqbn': fqbn, 'family': family, 'upload_log': '\n'.join(logs)
                }), 400
            ok, err_code, hint = _do_upload_avr(port, fqbn, hex_file, log)
            if ok:
                log("✓ Upload exitoso")
                return jsonify({
                    'ok': True, 'port': port, 'fqbn': fqbn, 'family': family,
                    'upload_log': '\n'.join(logs), 'logs': logs, 'message': 'Código subido exitosamente'
                })
            return err(err_code, 'Upload fallido', hint)

        elif family == 'esp32':
            build_dir, resolve_err = _resolve_bin_for_upload_esp32(data, temp_dir, log)
            if resolve_err:
                return jsonify({
                    'ok': False, 'error': resolve_err, 'logs': logs,
                    'port': port, 'fqbn': fqbn, 'family': family, 'upload_log': '\n'.join(logs)
                }), 400
            ok, strategy_used, err_code, hint, hints = _do_upload_esp32(port, fqbn, build_dir, log)
            if ok:
                log("✓ Upload ESP32 exitoso")
                return jsonify({
                    'ok': True, 'port': port, 'fqbn': fqbn, 'family': 'esp32',
                    'strategy_used': strategy_used, 'upload_log': '\n'.join(logs),
                    'logs': logs, 'hints': hints, 'message': 'Código subido exitosamente'
                })
            return jsonify({
                'ok': False, 'port': port, 'fqbn': fqbn, 'family': 'esp32',
                'strategy_used': strategy_used, 'upload_log': '\n'.join(logs),
                'logs': logs, 'hints': hints, 'error': hint or 'Upload fallido',
                'error_code': err_code or 'UPLOAD_FAIL', 'hint': hint
            }), 500

        # Family no soportada
        return jsonify({
            'ok': False, 'error': f'Family "{family}" no soportada para upload',
            'port': port, 'fqbn': fqbn, 'family': family, 'upload_log': '\n'.join(logs), 'logs': logs
        }), 501

    except subprocess.TimeoutExpired:
        log("Timeout durante el upload")
        return jsonify({
            'ok': False, 'error': 'Timeout', 'error_code': 'TIMEOUT',
            'port': data.get('port'), 'fqbn': data.get('fqbn'), 'family': family,
            'upload_log': '\n'.join(logs), 'logs': logs
        }), 408
    except Exception as e:
        log(f"Error inesperado: {str(e)}")
        return jsonify({
            'ok': False, 'error': str(e), 'error_code': 'UNEXPECTED_ERROR',
            'upload_log': '\n'.join(logs), 'logs': logs
        }), 500
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"[UPLOAD] Directorio temporal eliminado")
            except Exception as e:
                print(f"[UPLOAD] Error limpiando temp: {e}")

# ============================================
# ENDPOINT: GET / (info)
# ============================================

@app.route('/', methods=['GET'])
def index():
    """Información del Agent."""
    return jsonify({
        'name': 'MAX-IDE Agent',
        'version': VERSION,
        'description': 'Agente local para compilar y subir código a Arduino',
        'endpoints': {
            'GET /health': 'Estado del agent',
            'GET /ports': 'Lista de puertos seriales',
            'POST /compile': 'Compilar código (sin subir)',
            'POST /upload': 'Compilar y subir código al Arduino'
        },
        'arduino_cli': ARDUINO_CLI,
        'status': 'running'
    })

# ============================================
# MAIN
# ============================================

def main():
    parser = argparse.ArgumentParser(description='MAX-IDE Agent Local')
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT,
                        help=f'Puerto HTTP (default: {DEFAULT_PORT})')
    parser.add_argument('--host', '-H', type=str, default='127.0.0.1',
                        help='Host (default: 127.0.0.1)')
    parser.add_argument('--arduino-cli', type=str, default=None,
                        help='Ruta a arduino-cli')
    parser.add_argument('--debug', action='store_true',
                        help='Modo debug')
    
    args = parser.parse_args()
    
    # Override arduino-cli path si se especifica
    global ARDUINO_CLI
    if args.arduino_cli:
        ARDUINO_CLI = args.arduino_cli
    
    # Verificar arduino-cli
    print("=" * 50)
    print(f"MAX-IDE Agent v{VERSION}")
    print("=" * 50)
    
    if ARDUINO_CLI:
        print(f"✓ arduino-cli: {ARDUINO_CLI}")
    else:
        print("⚠ arduino-cli NO encontrado")
        print("  Instala desde: https://arduino.github.io/arduino-cli/")
        print("  O especifica la ruta con --arduino-cli")
    
    print(f"✓ Python: {platform.python_version()}")
    print(f"✓ Platform: {platform.platform()}")
    print(f"✓ Listening on: http://{args.host}:{args.port}")
    print("=" * 50)
    print("Endpoints:")
    print(f"  GET  http://{args.host}:{args.port}/health")
    print(f"  GET  http://{args.host}:{args.port}/ports")
    print(f"  POST http://{args.host}:{args.port}/upload")
    print("=" * 50)
    print("Presiona Ctrl+C para detener")
    print()
    
    # Ejecutar servidor
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)

if __name__ == '__main__':
    main()

