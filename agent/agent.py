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
from pathlib import Path
from datetime import datetime

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
    
    return jsonify({
        'ok': True,
        'version': VERSION,
        'ts': int(time.time()),
        'platform': platform.platform(),
        'arduino_cli': ARDUINO_CLI,
        'arduino_cli_version': cli_version,
        'python_version': platform.python_version()
    })

# ============================================
# ENDPOINT: GET /ports
# ============================================

@app.route('/ports', methods=['GET', 'OPTIONS'])
def list_ports():
    """
    Lista los puertos seriales disponibles.
    Filtra solo puertos USB reales (no virtuales del sistema).
    
    Response:
        {
            "ok": true,
            "ports": [
                {
                    "device": "/dev/ttyUSB0",
                    "name": "USB Serial",
                    "description": "USB Serial Device",
                    "vid": 6790,
                    "pid": 29987,
                    "serial_number": "12345",
                    "manufacturer": "1a86",
                    "product": "USB Serial"
                }
            ]
        }
    """
    # OPTIONS se maneja en before_request
    
    ports = []
    all_ports = []  # Para debug
    
    try:
        for port in serial.tools.list_ports.comports():
            # Filtrar solo puertos USB reales (excluir ttyS* virtuales)
            is_usb_port = (
                port.vid is not None or  # Tiene VID = dispositivo USB
                'USB' in (port.hwid or '') or
                'usb' in (port.device or '').lower() or
                'ACM' in (port.device or '')  # Arduino con CDC
            )
            
            # En Windows, incluir todos los COM
            if platform.system() == 'Windows':
                is_usb_port = True
            
            all_ports.append({
                'device': port.device,
                'vid': port.vid,
                'is_usb': is_usb_port
            })
            
            if not is_usb_port:
                continue
            
            port_info = {
                'device': port.device,
                'name': port.name,
                'description': port.description or 'USB Serial',
                'vid': port.vid,
                'pid': port.pid,
                'serial_number': port.serial_number,
                'manufacturer': port.manufacturer,
                'product': port.product,
                'hwid': port.hwid
            }
            
            # Identificar tipo de dispositivo y nombre amigable
            if port.vid == 0x2341 or port.vid == 0x2A03:
                port_info['type'] = 'arduino_official'
                port_info['friendly_name'] = 'Arduino Original'
            elif port.vid == 0x1A86:
                port_info['type'] = 'ch340'
                port_info['friendly_name'] = 'Arduino (CH340)'
            elif port.vid == 0x0403:
                port_info['type'] = 'ftdi'
                port_info['friendly_name'] = 'Arduino (FTDI)'
            elif port.vid == 0x10C4:
                port_info['type'] = 'cp210x'
                port_info['friendly_name'] = 'Arduino (CP2102)'
            elif port.vid == 0x239A:
                port_info['type'] = 'adafruit'
                port_info['friendly_name'] = 'Adafruit'
            elif port.vid == 0x1B4F:
                port_info['type'] = 'sparkfun'
                port_info['friendly_name'] = 'SparkFun'
            else:
                port_info['type'] = 'generic'
                port_info['friendly_name'] = port.description or 'USB Serial'
            
            ports.append(port_info)
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': f'Error listando puertos: {str(e)}',
            'ports': []
        }), 500
    
    return jsonify({
        'ok': True,
        'ports': ports,
        'count': len(ports),
        'total_scanned': len(all_ports)
    })

# ============================================
# ENDPOINT: POST /compile
# ============================================

@app.route('/compile', methods=['POST', 'OPTIONS'])
def compile_code():
    """
    Compila código Arduino sin subirlo.
    Útil para verificar que el código es correcto.
    
    Request body:
        {
            "code": "void setup() {} void loop() {}",
            "fqbn": "arduino:avr:uno"
        }
    
    Response:
        {
            "ok": true/false,
            "logs": ["log1", "log2", ...],
            "size": 1234,
            "message": "..."
        }
    """
    # OPTIONS se maneja en before_request
    
    logs = []
    temp_dir = None
    
    def log(msg):
        """Añade mensaje al log."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {msg}"
        logs.append(log_entry)
        print(f"[COMPILE] {msg}")
    
    try:
        # Verificar que arduino-cli esté disponible
        if not ARDUINO_CLI:
            return jsonify({
                'ok': False,
                'error': 'arduino-cli no encontrado. Instálalo desde https://arduino.github.io/arduino-cli/',
                'logs': logs,
                'hint': 'Ejecuta: curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh'
            }), 500
        
        # Parsear request
        data = request.get_json()
        if not data:
            return jsonify({
                'ok': False,
                'error': 'JSON body requerido',
                'logs': logs
            }), 400
        
        code = data.get('code', '')
        fqbn = data.get('fqbn', 'arduino:avr:uno')
        
        if not code or not code.strip():
            return jsonify({
                'ok': False,
                'error': 'No hay código para compilar',
                'logs': logs
            }), 400
        
        log(f"Iniciando compilación para {fqbn}")
        log(f"arduino-cli: {ARDUINO_CLI}")
        
        # Crear directorio temporal
        # Si arduino-cli es snap, usar ~/snap/arduino-cli/common/ que snap puede acceder
        # Si no, usar ~/.maxide-agent/tmp/
        if ARDUINO_CLI and 'snap' in ARDUINO_CLI:
            home_tmp = os.path.join(os.path.expanduser('~'), 'snap', 'arduino-cli', 'common', 'maxide-tmp')
        else:
            home_tmp = os.path.join(os.path.expanduser('~'), '.maxide-agent', 'tmp')
        os.makedirs(home_tmp, exist_ok=True)
        temp_dir = tempfile.mkdtemp(prefix='compile_', dir=home_tmp)
        
        # Crear sketch
        sketch_name = 'sketch_verify'
        sketch_dir = os.path.join(temp_dir, sketch_name)
        os.makedirs(sketch_dir)
        
        sketch_file = os.path.join(sketch_dir, f'{sketch_name}.ino')
        with open(sketch_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        log(f"Sketch creado: {len(code)} caracteres")
        
        # Compilar
        build_dir = os.path.join(temp_dir, 'build')
        os.makedirs(build_dir)
        
        compile_cmd = [
            ARDUINO_CLI, 'compile',
            '--fqbn', fqbn,
            '--output-dir', build_dir,
            sketch_dir
        ]
        
        log(f"Compilando...")
        
        compile_result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Capturar salida
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
            return jsonify({
                'ok': False,
                'error': error_msg,
                'logs': logs,
                'exit_code': compile_result.returncode
            }), 400
        
        # Buscar archivo HEX para obtener tamaño
        hex_size = 0
        for f in os.listdir(build_dir):
            if f.endswith('.hex'):
                hex_path = os.path.join(build_dir, f)
                hex_size = os.path.getsize(hex_path)
                break
        
        log(f"✓ Compilación exitosa ({hex_size} bytes)")
        
        return jsonify({
            'ok': True,
            'message': 'Compilación exitosa',
            'logs': logs,
            'size': hex_size,
            'fqbn': fqbn
        })
        
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
        # Limpiar directorio temporal
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"[COMPILE] Error limpiando temp: {e}")

# ============================================
# ENDPOINT: POST /upload
# ============================================

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload():
    """
    Sube código al Arduino.
    
    Request body:
        {
            "port": "/dev/ttyUSB0",
            "fqbn": "arduino:avr:uno",
            "hex_url": "https://example.com/api/hex/abc123.hex"
        }
        
        O alternativamente:
        {
            "port": "/dev/ttyUSB0",
            "fqbn": "arduino:avr:uno",
            "code": "void setup() {} void loop() {}"
        }
    
    Response:
        {
            "ok": true/false,
            "logs": ["log1", "log2", ...],
            "exit_code": 0,
            "detected": {"port": "...", "fqbn": "..."},
            "hint": "..."
        }
    """
    # OPTIONS se maneja en before_request
    
    logs = []
    temp_dir = None
    
    def log(msg):
        """Añade mensaje al log."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {msg}"
        logs.append(log_entry)
        print(f"[UPLOAD] {msg}")
    
    try:
        # Verificar que arduino-cli esté disponible
        if not ARDUINO_CLI:
            return jsonify({
                'ok': False,
                'error': 'arduino-cli no encontrado',
                'logs': logs,
                'hint': 'Instala arduino-cli: https://arduino.github.io/arduino-cli/'
            }), 500
        
        # Parsear request
        data = request.get_json()
        if not data:
            return jsonify({
                'ok': False,
                'error': 'JSON body requerido',
                'logs': logs
            }), 400
        
        port = data.get('port')
        fqbn = data.get('fqbn', 'arduino:avr:uno')
        hex_url = data.get('hex_url')
        code = data.get('code')
        
        # Validar parámetros
        if not port:
            return jsonify({
                'ok': False,
                'error': 'Parámetro "port" requerido',
                'logs': logs
            }), 400
        
        if not hex_url and not code:
            return jsonify({
                'ok': False,
                'error': 'Parámetro "hex_url" o "code" requerido',
                'logs': logs
            }), 400
        
        log(f"Iniciando upload a {port} con {fqbn}")
        
        # Crear directorio temporal
        # Si arduino-cli es snap, usar ~/snap/arduino-cli/common/ que snap puede acceder
        if ARDUINO_CLI and 'snap' in ARDUINO_CLI:
            home_tmp = os.path.join(os.path.expanduser('~'), 'snap', 'arduino-cli', 'common', 'maxide-tmp')
        else:
            home_tmp = os.path.join(os.path.expanduser('~'), '.maxide-agent', 'tmp')
        os.makedirs(home_tmp, exist_ok=True)
        temp_dir = tempfile.mkdtemp(prefix='upload_', dir=home_tmp)
        log(f"Directorio temporal: {temp_dir}")
        
        hex_file = None
        
        # ========================================
        # OPCIÓN 1: Descargar HEX desde URL
        # ========================================
        if hex_url:
            log(f"Descargando HEX desde: {hex_url}")
            
            try:
                response = requests.get(hex_url, timeout=30, stream=True)
                response.raise_for_status()
                
                # Validar Content-Type (opcional)
                content_type = response.headers.get('Content-Type', '')
                log(f"Content-Type: {content_type}")
                
                # Guardar archivo HEX
                hex_file = os.path.join(temp_dir, 'firmware.hex')
                
                total_size = 0
                with open(hex_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            total_size += len(chunk)
                
                log(f"HEX descargado: {total_size} bytes")
                
                # Validar tamaño
                if total_size == 0:
                    return jsonify({
                        'ok': False,
                        'error': 'Archivo HEX vacío',
                        'logs': logs,
                        'hint': 'El servidor retornó un archivo vacío. Verifica la compilación.'
                    }), 400
                
            except requests.Timeout:
                return jsonify({
                    'ok': False,
                    'error': 'Timeout descargando HEX',
                    'logs': logs,
                    'hint': 'El servidor tardó demasiado. Intenta de nuevo.'
                }), 408
            except requests.RequestException as e:
                return jsonify({
                    'ok': False,
                    'error': f'Error descargando HEX: {str(e)}',
                    'logs': logs
                }), 500
        
        # ========================================
        # OPCIÓN 2: Compilar código localmente
        # ========================================
        elif code:
            log("Compilando código localmente...")
            
            # Crear sketch
            sketch_name = 'sketch_upload'
            sketch_dir = os.path.join(temp_dir, sketch_name)
            os.makedirs(sketch_dir)
            
            sketch_file = os.path.join(sketch_dir, f'{sketch_name}.ino')
            with open(sketch_file, 'w') as f:
                f.write(code)
            
            log(f"Sketch creado: {sketch_file}")
            
            # Compilar
            build_dir = os.path.join(temp_dir, 'build')
            compile_cmd = [
                ARDUINO_CLI, 'compile',
                '--fqbn', fqbn,
                '--output-dir', build_dir,
                sketch_dir
            ]
            
            log(f"Ejecutando: {' '.join(compile_cmd)}")
            
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if compile_result.returncode != 0:
                error_msg = compile_result.stderr or compile_result.stdout
                log(f"Error de compilación: {error_msg[:500]}")
                return jsonify({
                    'ok': False,
                    'error': 'Error de compilación',
                    'logs': logs + [error_msg],
                    'exit_code': compile_result.returncode,
                    'hint': 'Verifica el código Arduino.'
                }), 400
            
            log("Compilación exitosa")
            
            # Buscar archivo HEX
            for f in os.listdir(build_dir):
                if f.endswith('.hex'):
                    hex_file = os.path.join(build_dir, f)
                    break
            
            if not hex_file:
                return jsonify({
                    'ok': False,
                    'error': 'No se generó archivo HEX',
                    'logs': logs
                }), 500
            
            log(f"HEX generado: {hex_file}")
        
        # ========================================
        # RESET PORT: Limpiar puerto antes de upload
        # ========================================
        log("Limpiando puerto serial antes de upload...")
        port_reset_ok = reset_serial_port(port, log)
        if not port_reset_ok:
            log("⚠ No se pudo limpiar el puerto, intentando upload de todos modos...")
        else:
            log("✓ Puerto limpiado correctamente")
        
        # Pequeño delay adicional para asegurar estabilidad
        time.sleep(0.3)
        
        # ========================================
        # UPLOAD: Ejecutar arduino-cli upload (con reintentos)
        # ========================================
        MAX_RETRIES = 2
        retry_count = 0
        upload_result = None
        
        upload_cmd = [
            ARDUINO_CLI, 'upload',
            '-p', port,
            '--fqbn', fqbn,
            '--input-file', hex_file,
            '-v'  # Verbose
        ]
        
        while retry_count <= MAX_RETRIES:
            if retry_count > 0:
                log(f"🔄 Reintento {retry_count}/{MAX_RETRIES}...")
                # Esperar antes de reintentar
                time.sleep(1.5)
                # Intentar limpiar el puerto de nuevo
                reset_serial_port(port, log)
                time.sleep(0.5)
            
            log(f"Ejecutando upload a {port}...")
            log(f"Comando: {' '.join(upload_cmd)}")
            
            upload_result = subprocess.run(
                upload_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Si fue exitoso, salir del loop
            if upload_result.returncode == 0:
                break
            
            # Verificar si el error es transitorio (puede mejorar con reintento)
            error_output = (upload_result.stderr + upload_result.stdout).lower()
            is_transient_error = any(x in error_output for x in [
                'busy', 'in use', 'resource busy', 'com-state',
                'timeout', 'timed out', "can't open device"
            ])
            
            if is_transient_error and retry_count < MAX_RETRIES:
                log(f"⚠ Error transitorio detectado, reintentando...")
                retry_count += 1
            else:
                # Error no transitorio o ya se acabaron los reintentos
                break
        
        # Capturar output completo
        stdout_lines = upload_result.stdout.strip().split('\n') if upload_result.stdout else []
        stderr_lines = upload_result.stderr.strip().split('\n') if upload_result.stderr else []
        
        # Añadir al log (últimas líneas)
        for line in stdout_lines[-30:]:
            if line.strip():
                logs.append(f"[stdout] {line}")
        
        for line in stderr_lines[-30:]:
            if line.strip():
                logs.append(f"[stderr] {line}")
        
        # Analizar resultado
        if upload_result.returncode == 0:
            log("✓ Upload exitoso!")
            return jsonify({
                'ok': True,
                'success': True,
                'message': 'Código subido exitosamente',
                'logs': logs,
                'exit_code': 0,
                'detected': {
                    'port': port,
                    'fqbn': fqbn
                }
            })
        else:
            # Analizar error y dar hint
            error_output = upload_result.stderr + upload_result.stdout
            error_lower = error_output.lower()
            
            hint = None
            error_code = 'UPLOAD_FAIL'
            
            # Error específico de Windows: can't set com-state
            if "can't set com-state" in error_lower or 'com-state' in error_lower:
                hint = '⚠️ Error de comunicación con el puerto (COM-state).\n' \
                       'Posibles soluciones:\n' \
                       '1. Desconecta y reconecta el cable USB\n' \
                       '2. Prueba otro puerto USB (preferiblemente USB 2.0)\n' \
                       '3. Si es Arduino Nano (clon CH340), selecciona "Arduino Nano (Old Bootloader)"\n' \
                       '4. Cierra todas las aplicaciones que puedan usar el puerto\n' \
                       '5. Reinicia el PC si el problema persiste\n' \
                       '6. Prueba con otro cable USB (algunos solo cargan, no transmiten datos)'
                error_code = 'COM_STATE_ERROR'
            
            # Puerto ocupado
            elif 'busy' in error_lower or 'in use' in error_lower or 'resource busy' in error_lower:
                hint = 'El puerto está ocupado. Cierra el Serial Monitor, Arduino IDE u otras aplicaciones que usen el puerto.'
                error_code = 'PORT_BUSY'
            
            # Error de sincronización
            elif 'sync' in error_lower or 'not in sync' in error_lower or 'programmer is not responding' in error_lower:
                hint = '⚠️ Error de sincronización con el bootloader.\n' \
                       'Posibles soluciones:\n' \
                       '1. Si es Arduino Nano (clon CH340), selecciona "Arduino Nano (Old Bootloader)" ← MÁS COMÚN\n' \
                       '2. Prueba con otro cable USB (que soporte datos, no solo carga)\n' \
                       '3. Evita usar hubs USB, conecta directo\n' \
                       '4. Instala los drivers CH340 si no los tienes\n' \
                       '5. Presiona RESET en la placa justo antes de subir\n' \
                       '6. Prueba otro puerto USB'
                error_code = 'SYNC_FAIL'
            
            # Puerto no encontrado
            elif 'no such file' in error_lower or 'not found' in error_lower or "can't open device" in error_lower:
                hint = 'Puerto no encontrado. Verifica que el Arduino esté conectado y el cable funcione.'
                error_code = 'PORT_NOT_FOUND'
            
            # Permisos
            elif 'permission denied' in error_lower or 'access denied' in error_lower:
                if platform.system() == 'Linux':
                    # Detectar si es problema de snap
                    if ARDUINO_CLI and 'snap' in ARDUINO_CLI:
                        hint = '⚠️ arduino-cli (snap) no puede acceder a puertos seriales.\n' \
                               'Solución: Instala arduino-cli SIN snap:\n' \
                               '  sudo snap remove arduino-cli\n' \
                               '  curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh\n' \
                               '  sudo mv bin/arduino-cli /usr/local/bin/\n' \
                               '  arduino-cli core install arduino:avr\n' \
                               'Luego reinicia el Agent.'
                    else:
                        hint = 'Permiso denegado. Ejecuta:\n  sudo usermod -a -G dialout $USER\nY luego cierra sesión y vuelve a entrar.'
                else:
                    hint = 'Permiso denegado. Ejecuta el Agent como administrador o verifica permisos del puerto.'
                error_code = 'PERMISSION_DENIED'
            
            # Timeout
            elif 'timeout' in error_lower or 'timed out' in error_lower:
                hint = 'Timeout durante el upload. Verifica la conexión y reinicia el Arduino.'
                error_code = 'TIMEOUT'
            
            # Error genérico
            else:
                hint = 'Error durante el upload. Revisa los logs para más detalles.'
            
            log(f"✗ Upload fallido: {error_code}")
            
            return jsonify({
                'ok': False,
                'success': False,
                'error': error_output[:2000],
                'error_code': error_code,
                'logs': logs,
                'exit_code': upload_result.returncode,
                'detected': {
                    'port': port,
                    'fqbn': fqbn
                },
                'hint': hint
            }), 500
    
    except subprocess.TimeoutExpired:
        log("✗ Timeout durante la operación")
        return jsonify({
            'ok': False,
            'error': 'Timeout durante el upload',
            'error_code': 'TIMEOUT',
            'logs': logs,
            'hint': 'La operación tardó demasiado. Verifica la conexión con el Arduino.'
        }), 408
    
    except json.JSONDecodeError:
        return jsonify({
            'ok': False,
            'error': 'JSON inválido en el body',
            'logs': logs
        }), 400
    
    except Exception as e:
        log(f"✗ Error inesperado: {str(e)}")
        return jsonify({
            'ok': False,
            'error': str(e),
            'error_code': 'UNEXPECTED_ERROR',
            'logs': logs
        }), 500
    
    finally:
        # ========================================
        # LIMPIEZA: Eliminar archivos temporales
        # ========================================
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"[CLEANUP] Directorio temporal eliminado: {temp_dir}")
            except Exception as e:
                print(f"[CLEANUP] Error eliminando temporal: {e}")

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

