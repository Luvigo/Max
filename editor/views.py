import json
import os
import subprocess
import shutil
import uuid
import threading
import re
import base64
import time
import secrets
from pathlib import Path
from datetime import datetime, timedelta

from django.http import JsonResponse, FileResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

import serial
import serial.tools.list_ports

# Rutas importantes
BASE_DIR = Path(settings.BASE_DIR)
SKETCH_DIR = BASE_DIR / 'sketches'
SKETCH_DIR.mkdir(exist_ok=True)

# Directorio para HEX temporales
HEX_TEMP_DIR = BASE_DIR / 'hex_temp'
HEX_TEMP_DIR.mkdir(exist_ok=True)

# Almacenamiento de tokens HEX (token -> {path, expires, fqbn, size})
# En producción, considera usar Redis o base de datos
hex_tokens = {}
hex_tokens_lock = threading.Lock()

# Tiempo de expiración de tokens HEX (en segundos)
HEX_TOKEN_EXPIRY = 600  # 10 minutos

# Directorio de datos de Arduino (para que persista en Render)
ARDUINO_DATA_DIR = BASE_DIR / 'arduino-data'
ARDUINO_DATA_DIR.mkdir(exist_ok=True)

# Arduino CLI path - buscar en diferentes ubicaciones
def find_arduino_cli():
    """Busca arduino-cli en diferentes ubicaciones."""
    possible_paths = [
        BASE_DIR / 'bin' / 'arduino-cli',  # Render / Local con bin
        Path('/usr/local/bin/arduino-cli'),  # Sistema
        Path('/usr/bin/arduino-cli'),  # Sistema alternativo
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    # Intentar encontrar en PATH
    import shutil as sh
    which_result = sh.which('arduino-cli')
    if which_result:
        return which_result
    
    # Fallback al path local
    return str(BASE_DIR / 'bin' / 'arduino-cli')

ARDUINO_CLI = find_arduino_cli()

# ============================================
# GESTIÓN DE TOKENS HEX
# ============================================

def generate_hex_token():
    """Genera un token único y seguro para un archivo HEX."""
    return secrets.token_urlsafe(32)


def cleanup_expired_tokens():
    """Elimina tokens expirados y sus archivos."""
    now = datetime.now()
    expired = []
    
    with hex_tokens_lock:
        for token, data in list(hex_tokens.items()):
            if data['expires'] < now:
                expired.append(token)
                # Eliminar archivo HEX
                try:
                    hex_path = Path(data['path'])
                    if hex_path.exists():
                        hex_path.unlink()
                except Exception as e:
                    print(f"[HEX-CLEANUP] Error eliminando {data['path']}: {e}")
        
        # Eliminar tokens del diccionario
        for token in expired:
            del hex_tokens[token]
    
    if expired:
        print(f"[HEX-CLEANUP] Eliminados {len(expired)} tokens expirados")


def store_hex_token(hex_path, fqbn, size):
    """
    Almacena un token para un archivo HEX.
    
    Returns:
        str: Token generado
    """
    # Limpiar tokens expirados ocasionalmente
    if len(hex_tokens) > 50:  # Cada 50 compilaciones
        cleanup_expired_tokens()
    
    token = generate_hex_token()
    expires = datetime.now() + timedelta(seconds=HEX_TOKEN_EXPIRY)
    
    with hex_tokens_lock:
        hex_tokens[token] = {
            'path': str(hex_path),
            'expires': expires,
            'fqbn': fqbn,
            'size': size,
            'created': datetime.now()
        }
    
    return token


def get_hex_by_token(token):
    """
    Obtiene la información de un HEX por su token.
    
    Returns:
        dict o None: Datos del HEX si es válido, None si no existe o expiró
    """
    cleanup_expired_tokens()  # Limpiar expirados
    
    with hex_tokens_lock:
        data = hex_tokens.get(token)
        
        if not data:
            return None
        
        # Verificar expiración
        if data['expires'] < datetime.now():
            # Eliminar token expirado
            del hex_tokens[token]
            try:
                Path(data['path']).unlink()
            except:
                pass
            return None
        
        return data


def invalidate_hex_token(token):
    """Invalida un token y elimina su archivo."""
    with hex_tokens_lock:
        data = hex_tokens.pop(token, None)
        if data:
            try:
                Path(data['path']).unlink()
            except:
                pass


# Variables de entorno para arduino-cli (usar directorio del proyecto)
ARDUINO_ENV = os.environ.copy()
ARDUINO_ENV['ARDUINO_DATA_DIR'] = str(ARDUINO_DATA_DIR)
ARDUINO_ENV['ARDUINO_DOWNLOADS_DIR'] = str(ARDUINO_DATA_DIR / 'staging')
ARDUINO_ENV['ARDUINO_SKETCHBOOK_DIR'] = str(SKETCH_DIR)

# Conexión serial global
serial_connection = None
serial_lock = threading.Lock()

# Lock global para uploads (evitar uploads concurrentes)
upload_lock = threading.Lock()
# Lock por puerto (diccionario de locks)
port_locks = {}
port_locks_mutex = threading.Lock()

def get_port_lock(port):
    """Obtiene o crea un lock para un puerto específico."""
    with port_locks_mutex:
        if port not in port_locks:
            port_locks[port] = threading.Lock()
        return port_locks[port]

def detect_device_type(port_info):
    """
    Detecta el tipo de dispositivo basado en VID/PID y metadata.
    
    Returns:
        dict con: device_type, is_arduino, is_ch340, suggested_board, warning
    """
    vid = port_info.get('vid')
    pid = port_info.get('pid')
    description = (port_info.get('description') or '').lower()
    product = (port_info.get('product') or '').lower()
    manufacturer = (port_info.get('manufacturer') or '').lower()
    
    # VID/PID conocidos
    ARDUINO_VIDS = [0x2341, 0x2A03, 0x239A]  # Arduino LLC, Arduino.org, Adafruit
    CH340_VID = 0x1A86
    FTDI_VID = 0x0403
    CP210X_VID = 0x10C4
    
    is_arduino = vid in ARDUINO_VIDS
    is_ch340 = vid == CH340_VID
    is_ftdi = vid == FTDI_VID
    is_cp210x = vid == CP210X_VID
    
    device_type = 'unknown'
    suggested_board = None
    warning = None
    
    if is_arduino:
        device_type = 'arduino_official'
        # Detectar placa específica por descripción
        if 'uno' in description or 'uno' in product:
            suggested_board = 'arduino:avr:uno'
        elif 'nano' in description or 'nano' in product:
            suggested_board = 'arduino:avr:nano'
        elif 'mega' in description or 'mega' in product:
            suggested_board = 'arduino:avr:mega'
        elif 'leonardo' in description or 'leonardo' in product:
            suggested_board = 'arduino:avr:leonardo'
    elif is_ch340:
        device_type = 'ch340'
        # CH340 típicamente se usa en clones de Nano/UNO
        if 'nano' in description or 'nano' in product:
            suggested_board = 'arduino:avr:nano'
            warning = 'Dispositivo CH340 detectado. Si es un Nano clon, prueba con "Arduino Nano (Old Bootloader)" si el upload falla.'
        else:
            suggested_board = 'arduino:avr:nano'  # Por defecto, muchos clones CH340 son Nano
            warning = 'Dispositivo CH340 detectado (típicamente Nano clon). Considera usar "Arduino Nano (Old Bootloader)".'
    elif is_ftdi:
        device_type = 'ftdi'
    elif is_cp210x:
        device_type = 'cp210x'
    else:
        device_type = 'unknown'
        warning = 'Dispositivo USB serial no reconocido. Verifica que sea un Arduino o placa compatible.'
    
    return {
        'device_type': device_type,
        'is_arduino': is_arduino,
        'is_ch340': is_ch340,
        'is_ftdi': is_ftdi,
        'is_cp210x': is_cp210x,
        'suggested_board': suggested_board,
        'warning': warning
    }


def validate_port_exists(port):
    """Valida que el puerto existe y es accesible."""
    import os
    import stat
    
    # En Linux/Mac, verificar que el dispositivo existe
    if os.path.exists(port):
        try:
            mode = os.stat(port).st_mode
            # Verificar que es un dispositivo de caracteres (puerto serial)
            if stat.S_ISCHR(mode):
                return True, None
            else:
                return False, f"El puerto {port} no es un dispositivo serial válido"
        except OSError as e:
            return False, f"No se puede acceder al puerto {port}: {str(e)}"
    
    # En Windows, los puertos COM no aparecen como archivos
    if port.upper().startswith('COM'):
        # Intentar listar puertos disponibles
        try:
            available = [p.device for p in serial.tools.list_ports.comports()]
            if port in available or port.upper() in [p.upper() for p in available]:
                return True, None
            else:
                return False, f"Puerto {port} no encontrado. Disponibles: {', '.join(available) if available else 'ninguno'}"
        except Exception as e:
            return False, f"Error verificando puerto: {str(e)}"
    
    return False, f"Puerto {port} no existe"


def get_port_info(port):
    """Obtiene información completa de un puerto."""
    try:
        for p in serial.tools.list_ports.comports():
            if p.device == port:
                return {
                    'device': p.device,
                    'description': p.description,
                    'vid': p.vid,
                    'pid': p.pid,
                    'serial_number': p.serial_number,
                    'manufacturer': p.manufacturer,
                    'product': p.product,
                    'hwid': p.hwid
                }
    except Exception:
        pass
    return None

def close_serial_connection():
    """Cierra la conexión serial global si está abierta."""
    global serial_connection
    closed = False
    with serial_lock:
        if serial_connection:
            try:
                if serial_connection.is_open:
                    serial_connection.close()
                    closed = True
            except Exception as e:
                print(f"[UPLOAD] Error cerrando conexión serial: {e}")
            serial_connection = None
    return closed


def reset_arduino_dtr(port, log_func=None):
    """
    Fuerza un reset del Arduino mediante toggle de DTR/RTS.
    
    Esto pone al Arduino en modo bootloader antes de que arduino-cli
    intente comunicarse con él, mejorando la tasa de éxito en uploads
    repetidos.
    
    Args:
        port: Puerto serial (ej: /dev/ttyUSB0, COM3)
        log_func: Función opcional para logging
        
    Returns:
        tuple: (success: bool, message: str)
    """
    def log(msg):
        if log_func:
            log_func(msg)
        print(f"[RESET] {msg}")
    
    try:
        log(f"Iniciando reset DTR/RTS en {port}")
        
        # Abrir puerto a 1200 baud (trigger especial para algunos bootloaders)
        # Para UNO/Mega, el baudrate no importa tanto, es el toggle de DTR
        ser = serial.Serial()
        ser.port = port
        ser.baudrate = 1200
        ser.timeout = 0.1
        ser.write_timeout = 0.1
        
        # Configurar sin abrir aún
        ser.dtr = False
        ser.rts = False
        
        try:
            ser.open()
        except serial.SerialException as e:
            # Si falla a 1200, intentar a 9600 (más compatible)
            log(f"No se pudo abrir a 1200 baud, intentando 9600: {e}")
            ser.baudrate = 9600
            try:
                ser.open()
            except serial.SerialException as e2:
                log(f"Error abriendo puerto: {e2}")
                return False, str(e2)
        
        log("Puerto abierto, ejecutando secuencia de reset...")
        
        # Secuencia de reset para Arduino UNO/Mega/Nano (ATmega328/2560)
        # El bootloader se activa cuando DTR hace una transición LOW->HIGH
        
        # 1. DTR y RTS a LOW
        ser.dtr = False
        ser.rts = False
        time.sleep(0.05)
        
        # 2. DTR a HIGH (esto genera el pulso de reset via capacitor en el Arduino)
        ser.dtr = True
        time.sleep(0.05)
        
        # 3. DTR a LOW de nuevo
        ser.dtr = False
        time.sleep(0.05)
        
        # 4. Alternativamente, algunos clones necesitan RTS
        ser.rts = True
        time.sleep(0.05)
        ser.rts = False
        
        # Cerrar el puerto
        ser.close()
        log("Puerto cerrado después del reset")
        
        # Esperar a que el bootloader inicie (típicamente 200-500ms)
        # El bootloader del Arduino espera ~1 segundo antes de ejecutar el sketch
        wait_time = 0.5  # 500ms
        log(f"Esperando {int(wait_time*1000)}ms para que el bootloader inicie...")
        time.sleep(wait_time)
        
        log("Reset completado exitosamente")
        return True, "Reset DTR/RTS completado"
        
    except Exception as e:
        log(f"Error durante reset: {str(e)}")
        return False, str(e)


def index(request):
    """Vista principal del IDE."""
    # Permitir acceso directo al editor si viene con parámetro 'editor=true' o desde un enlace explícito
    # Solo redirigir automáticamente si viene de la raíz sin intención explícita
    force_editor = request.GET.get('editor') == 'true'
    
    # Si el usuario está autenticado y NO viene explícitamente al editor, redirigir a su dashboard
    if request.user.is_authenticated and not force_editor:
        try:
            if request.user.student_profile:
                # Solo redirigir si viene de la raíz sin parámetros
                if not request.GET and request.path == '/':
                    return redirect('editor:student_dashboard')
        except:
            pass
        # Si es admin y viene de la raíz, redirigir a admin dashboard
        if request.user.is_staff or request.user.is_superuser:
            if not request.GET and request.path == '/':
                return redirect('editor:admin_dashboard')
    
    # Mostrar el editor (todos pueden acceder si vienen explícitamente)
    project_id = request.GET.get('project_id')
    project = None
    project_xml = ''
    project_code = ''
    
    if project_id and request.user.is_authenticated:
        try:
            from .models import Project
            student = request.user.student_profile
            project = Project.objects.get(id=project_id, student=student, is_active=True)
            project_xml = project.xml_content
            project_code = project.arduino_code
        except:
            pass
    
    return render(request, 'editor/index.html', {
        'project': project,
        'project_xml': project_xml,
        'project_code': project_code,
        'now': int(time.time())  # Cache busting
    })


@require_http_methods(["GET"])
def list_ports(request):
    """Lista los puertos usando arduino-cli (multiplataforma)."""
    ports = []
    
    try:
        # Usar arduino-cli board list para detectar puertos
        result = subprocess.run(
            [ARDUINO_CLI, 'board', 'list', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=10,
            env=ARDUINO_ENV
        )
        
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            
            # arduino-cli devuelve una lista de puertos detectados
            detected_ports = data if isinstance(data, list) else data.get('detected_ports', [])
            
            for item in detected_ports:
                port_info = item.get('port', item) if isinstance(item, dict) else {}
                
                # Obtener información del puerto
                address = port_info.get('address', '') or item.get('address', '')
                protocol = port_info.get('protocol', '') or item.get('protocol', 'serial')
                label = port_info.get('label', '') or port_info.get('protocol_label', '') or ''
                
                # Obtener información de la placa si está disponible
                boards = item.get('matching_boards', []) or item.get('boards', [])
                board_name = ''
                board_fqbn = ''
                
                if boards and len(boards) > 0:
                    board_name = boards[0].get('name', '')
                    board_fqbn = boards[0].get('fqbn', '')
                
                # Solo incluir puertos seriales
                if protocol in ['serial', 'serialport', ''] and address:
                    description = board_name if board_name else label
                    if not description:
                        description = f"Puerto Serial ({protocol})"
                    
                    ports.append({
                        'device': address,
                        'description': description,
                        'protocol': protocol,
                        'board_name': board_name,
                        'board_fqbn': board_fqbn,
                        'hwid': label
                    })
    
    except subprocess.TimeoutExpired:
        pass
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    except Exception as e:
        print(f"Error arduino-cli: {e}")
    
    # Fallback: usar pyserial si arduino-cli no encontró puertos
    # También usar pyserial para obtener metadata completa (vid, pid, serial)
    try:
        pyserial_ports = {p.device: p for p in serial.tools.list_ports.comports()}
        
        # Enriquecer puertos existentes con metadata de pyserial
        for port in ports:
            device = port.get('device', '')
            if device in pyserial_ports:
                p = pyserial_ports[device]
                port['vid'] = p.vid
                port['pid'] = p.pid
                port['serial_number'] = p.serial_number
                port['manufacturer'] = p.manufacturer
                port['product'] = p.product
                # Mejorar description si está vacía
                if not port.get('description') or port['description'] == 'Puerto Serial':
                    port['description'] = p.description or 'Puerto Serial'
        
        # Si no hay puertos de arduino-cli, agregar todos los de pyserial
        if not ports:
            for port in pyserial_ports.values():
                ports.append({
                    'device': port.device,
                    'description': port.description or 'Puerto Serial',
                    'protocol': 'serial',
                    'board_name': '',
                    'board_fqbn': '',
                    'hwid': port.hwid or '',
                    'vid': port.vid,
                    'pid': port.pid,
                    'serial_number': port.serial_number,
                    'manufacturer': port.manufacturer,
                    'product': port.product
                })
    except Exception as e:
        print(f"Error obteniendo metadata de puertos: {e}")
    
    return JsonResponse({'ports': ports})


@csrf_exempt
@require_http_methods(["POST"])
def compile_code(request):
    """
    Compila el código Arduino y genera un token para descargar el HEX.
    
    Input JSON:
        {
            "code": "void setup() {} void loop() {}",
            "fqbn": "arduino:avr:uno"  // o "board" para compatibilidad
        }
    
    Output JSON:
        {
            "ok": true,
            "token": "abc123...",
            "hex_url": "/api/hex/abc123.hex",
            "logs": ["Compilando...", "Éxito"],
            "size": 1234,
            "fqbn": "arduino:avr:uno"
        }
    """
    sketch_path = None
    logs = []
    
    def log(msg):
        timestamp = time.strftime('%H:%M:%S')
        logs.append(f"[{timestamp}] {msg}")
        print(f"[COMPILE] {msg}")
    
    try:
        data = json.loads(request.body)
        code = data.get('code', '') or data.get('sketch_ino_text', '')
        fqbn = data.get('fqbn', '') or data.get('board', 'arduino:avr:uno')
        
        if not code:
            return JsonResponse({
                'ok': False,
                'error': 'No se proporcionó código',
                'error_code': 'NO_CODE',
                'logs': logs
            }, status=400)
        
        log(f"Iniciando compilación para {fqbn}")
        log(f"Código recibido: {len(code)} caracteres")
        
        # Crear directorio único para el sketch
        sketch_id = str(uuid.uuid4())[:8]
        sketch_name = f'sketch_{sketch_id}'
        sketch_path = SKETCH_DIR / sketch_name
        sketch_path.mkdir(exist_ok=True)
        sketch_file = sketch_path / f'{sketch_name}.ino'
        
        # Escribir el código
        sketch_file.write_text(code)
        log(f"Sketch creado: {sketch_name}")
        
        # Directorio de build para obtener el .hex
        build_path = sketch_path / 'build'
        
        # Compilar usando arduino-cli
        log("Ejecutando arduino-cli compile...")
        result = subprocess.run(
            [
                ARDUINO_CLI, 'compile',
                '--fqbn', fqbn,
                '--output-dir', str(build_path),
                '--verbose',
                str(sketch_path)
            ],
            capture_output=True,
            text=True,
            timeout=120,
            env=ARDUINO_ENV
        )
        
        # Capturar logs de compilación
        if result.stdout:
            for line in result.stdout.strip().split('\n')[-15:]:
                if line.strip():
                    logs.append(f"[arduino-cli] {line.strip()}")
        
        if result.returncode == 0:
            log("Compilación exitosa")
            
            # Buscar el archivo .hex generado
            hex_file = None
            for f in build_path.iterdir():
                if f.suffix == '.hex':
                    hex_file = f
                    break
            
            if not hex_file or not hex_file.exists():
                log("ERROR: No se encontró archivo .hex")
                return JsonResponse({
                    'ok': False,
                    'error': 'Compilación exitosa pero no se generó archivo .hex',
                    'error_code': 'NO_HEX_GENERATED',
                    'logs': logs
                }, status=500)
            
            # Obtener tamaño del HEX
            hex_size = hex_file.stat().st_size
            log(f"Archivo HEX generado: {hex_size} bytes")
            
            # Mover el HEX al directorio temporal con nombre único
            hex_token = generate_hex_token()
            permanent_hex_path = HEX_TEMP_DIR / f"{hex_token}.hex"
            shutil.copy2(hex_file, permanent_hex_path)
            
            # Almacenar token
            store_hex_token(permanent_hex_path, fqbn, hex_size)
            
            log(f"Token generado: {hex_token[:16]}...")
            
            return JsonResponse({
                'ok': True,
                'success': True,  # Compatibilidad
                'token': hex_token,
                'hex_url': f'/api/hex/{hex_token}.hex',
                'logs': logs,
                'size': hex_size,
                'fqbn': fqbn,
                'message': 'Compilación exitosa'
            })
        else:
            # Error de compilación
            error_msg = result.stderr or result.stdout
            log(f"Error de compilación: {error_msg[:500]}")
            
            # Agregar errores al log
            if result.stderr:
                for line in result.stderr.strip().split('\n')[-20:]:
                    if line.strip():
                        logs.append(f"[error] {line.strip()}")
            
            return JsonResponse({
                'ok': False,
                'success': False,
                'error': error_msg,
                'error_code': 'COMPILE_ERROR',
                'logs': logs
            }, status=400)
            
    except subprocess.TimeoutExpired:
        log("Timeout de compilación (120s)")
        return JsonResponse({
            'ok': False,
            'error': 'Timeout de compilación',
            'error_code': 'TIMEOUT',
            'logs': logs
        }, status=408)
    except json.JSONDecodeError:
        return JsonResponse({
            'ok': False,
            'error': 'JSON inválido',
            'error_code': 'INVALID_JSON',
            'logs': logs
        }, status=400)
    except FileNotFoundError:
        log("arduino-cli no encontrado")
        return JsonResponse({
            'ok': False,
            'error': 'arduino-cli no encontrado. Verifica la instalación.',
            'error_code': 'CLI_NOT_FOUND',
            'logs': logs
        }, status=500)
    except Exception as e:
        log(f"Error inesperado: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': str(e),
            'error_code': 'UNEXPECTED_ERROR',
            'logs': logs
        }, status=500)
    finally:
        # Limpiar sketch temporal (pero NO el HEX, que está en hex_temp)
        if sketch_path and sketch_path.exists():
            try:
                shutil.rmtree(sketch_path)
            except:
                pass


# ============================================
# ENDPOINT: GET /api/hex/<token>.hex
# ============================================

@require_http_methods(["GET"])
def serve_hex_file(request, token):
    """
    Sirve un archivo HEX por su token.
    
    URL: GET /api/hex/<token>.hex
    
    Response:
        - 200: Archivo HEX con Content-Type: application/octet-stream
        - 404: Token no encontrado o expirado
        - 410: Token expirado (Gone)
    
    Headers de respuesta:
        - Content-Type: application/octet-stream
        - Content-Disposition: attachment; filename="firmware.hex"
        - Cache-Control: no-store, no-cache, must-revalidate
        - X-HEX-Size: <tamaño en bytes>
        - X-HEX-FQBN: <fqbn usado en compilación>
    """
    # Limpiar extensión .hex si viene en el token
    if token.endswith('.hex'):
        token = token[:-4]
    
    # Obtener datos del token
    hex_data = get_hex_by_token(token)
    
    if not hex_data:
        return JsonResponse({
            'ok': False,
            'error': 'Token no encontrado o expirado',
            'error_code': 'TOKEN_INVALID'
        }, status=404)
    
    hex_path = Path(hex_data['path'])
    
    if not hex_path.exists():
        # El archivo fue eliminado pero el token existe
        invalidate_hex_token(token)
        return JsonResponse({
            'ok': False,
            'error': 'Archivo HEX no disponible',
            'error_code': 'HEX_NOT_FOUND'
        }, status=410)
    
    # Servir el archivo
    try:
        response = FileResponse(
            open(hex_path, 'rb'),
            content_type='application/octet-stream'
        )
        
        # Headers
        response['Content-Disposition'] = 'attachment; filename="firmware.hex"'
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['X-HEX-Size'] = str(hex_data['size'])
        response['X-HEX-FQBN'] = hex_data['fqbn']
        response['X-HEX-Token'] = token[:16] + '...'
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'ok': False,
            'error': f'Error leyendo archivo HEX: {str(e)}',
            'error_code': 'READ_ERROR'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def compile_and_download(request):
    """Compila el código y devuelve el archivo .hex para subir desde el cliente."""
    sketch_path = None
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        board = data.get('board', 'arduino:avr:uno')
        
        if not code:
            return JsonResponse({'success': False, 'error': 'No code provided'}, status=400)
        
        # Crear directorio único para el sketch
        sketch_id = str(uuid.uuid4())[:8]
        sketch_name = f'sketch_{sketch_id}'
        sketch_path = SKETCH_DIR / sketch_name
        sketch_path.mkdir(exist_ok=True)
        sketch_file = sketch_path / f'{sketch_name}.ino'
        
        # Escribir el código
        sketch_file.write_text(code)
        
        # Compilar con output-dir para saber dónde quedan los binarios
        build_path = sketch_path / 'build'
        result = subprocess.run(
            [ARDUINO_CLI, 'compile', '--fqbn', board, 
             '--output-dir', str(build_path), str(sketch_path)],
            capture_output=True,
            text=True,
            timeout=120,
            env=ARDUINO_ENV
        )
        
        if result.returncode == 0:
            # Buscar el archivo .hex generado
            hex_file = None
            for f in build_path.iterdir():
                if f.suffix == '.hex':
                    hex_file = f
                    break
            
            if hex_file and hex_file.exists():
                # Leer el archivo hex y convertir a base64
                hex_content = hex_file.read_bytes()
                hex_base64 = base64.b64encode(hex_content).decode('utf-8')
                
                return JsonResponse({
                    'success': True,
                    'message': 'Compilación exitosa',
                    'hex_file': hex_base64,
                    'hex_filename': hex_file.name,
                    'output': result.stdout
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Compilación exitosa pero no se encontró archivo .hex',
                    'output': result.stdout
                })
        else:
            error_msg = result.stderr or result.stdout
            return JsonResponse({
                'success': False,
                'error': error_msg,
                'output': result.stdout
            })
            
    except subprocess.TimeoutExpired:
        return JsonResponse({'success': False, 'error': 'Timeout de compilación'}, status=408)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except FileNotFoundError:
        return JsonResponse({
            'success': False, 
            'error': 'arduino-cli no encontrado. Verifica la instalación.'
        }, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    finally:
        if sketch_path and sketch_path.exists():
            try:
                shutil.rmtree(sketch_path)
            except:
                pass


@csrf_exempt
@require_http_methods(["POST"])
def upload_code(request):
    """
    Compila y sube el código a la placa Arduino.
    
    Implementa:
    - Lock por puerto para evitar uploads concurrentes
    - Validación de puerto antes de subir
    - Cierre de conexión serial del servidor
    - Reintentos con espera progresiva si falla sync
    - Respuesta JSON estructurada con error_code
    """
    sketch_path = None
    logs = []
    
    def log(msg):
        """Agrega mensaje al log."""
        logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        print(f"[UPLOAD] {msg}")
    
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        port = data.get('port', '')
        board = data.get('board', 'arduino:avr:uno')
        
        # Validaciones básicas
        if not code:
            return JsonResponse({
                'ok': False,
                'error_code': 'NO_CODE',
                'error': 'No se proporcionó código',
                'details': {'port': port, 'fqbn': board},
                'logs': logs
            }, status=400)
        
        if not port:
            return JsonResponse({
                'ok': False,
                'error_code': 'NO_PORT',
                'error': 'No se especificó puerto',
                'details': {'port': None, 'fqbn': board},
                'logs': logs
            }, status=400)
        
        log(f"Iniciando upload a {port} con placa {board}")
        
        # ========================================
        # 1. VERIFICAR LOCK POR PUERTO
        # ========================================
        port_lock = get_port_lock(port)
        
        # Intentar adquirir el lock sin bloquear
        if not port_lock.acquire(blocking=False):
            log(f"Puerto {port} ocupado por otro upload")
            return JsonResponse({
                'ok': False,
                'error_code': 'PORT_BUSY',
                'error': f'Ya hay un upload en progreso en el puerto {port}. Espera a que termine.',
                'details': {'port': port, 'fqbn': board},
                'logs': logs
            }, status=409)
        
        try:
            # ========================================
            # 2. CERRAR CONEXIÓN SERIAL DEL SERVIDOR
            # ========================================
            if close_serial_connection():
                log("Conexión serial del servidor cerrada")
                time.sleep(0.2)  # Pequeña espera para liberar el puerto
            
            # ========================================
            # 3. VALIDAR QUE EL PUERTO EXISTE
            # ========================================
            port_valid, port_error = validate_port_exists(port)
            if not port_valid:
                log(f"Puerto no válido: {port_error}")
                return JsonResponse({
                    'ok': False,
                    'error_code': 'PORT_NOT_FOUND',
                    'error': port_error,
                    'details': {'port': port, 'fqbn': board},
                    'logs': logs
                }, status=404)
            
            log(f"Puerto {port} validado correctamente")
            
            # ========================================
            # 3.1 DETECTAR TIPO DE DISPOSITIVO Y VALIDAR
            # ========================================
            port_info = get_port_info(port)
            device_detection = None
            warning_message = None
            suggested_board_change = None
            
            if port_info:
                device_detection = detect_device_type(port_info)
                log(f"Dispositivo detectado: {device_detection['device_type']}")
                
                # Validar que sea un dispositivo Arduino/USB serial típico
                if not device_detection['is_arduino'] and not device_detection['is_ch340'] and \
                   not device_detection['is_ftdi'] and not device_detection['is_cp210x']:
                    warning_message = device_detection.get('warning', 'Dispositivo USB serial no reconocido. Verifica que sea un Arduino o placa compatible.')
                    log(f"Advertencia: {warning_message}")
                    # No abortamos, solo advertimos
                
                # Detectar incompatibilidad: UNO seleccionado pero dispositivo parece Nano (CH340)
                if board == 'arduino:avr:uno' and device_detection['is_ch340']:
                    if 'nano' in (port_info.get('description') or '').lower() or \
                       'nano' in (port_info.get('product') or '').lower():
                        warning_message = 'Dispositivo CH340 detectado que parece ser un Nano, pero tienes seleccionado Arduino UNO. Considera cambiar a "Arduino Nano (Old Bootloader)".'
                        suggested_board_change = 'arduino:avr:nano'
                        log(f"Advertencia: {warning_message}")
                    else:
                        warning_message = 'Dispositivo CH340 detectado. Si el upload falla, prueba con "Arduino Nano (Old Bootloader)".'
                        suggested_board_change = 'arduino:avr:nano'
                        log(f"Advertencia: {warning_message}")
                
                # Si el dispositivo sugiere una placa diferente
                if device_detection.get('suggested_board') and \
                   device_detection['suggested_board'] != board:
                    if not warning_message:  # Solo si no hay otra advertencia
                        warning_message = device_detection.get('warning', 
                            f'El dispositivo sugiere usar "{device_detection["suggested_board"]}" pero tienes seleccionado "{board}".')
                        suggested_board_change = device_detection['suggested_board']
            
            # ========================================
            # 4. CREAR SKETCH Y COMPILAR
            # ========================================
            sketch_id = str(uuid.uuid4())[:8]
            sketch_name = f'sketch_{sketch_id}'
            sketch_path = SKETCH_DIR / sketch_name
            sketch_path.mkdir(exist_ok=True)
            sketch_file = sketch_path / f'{sketch_name}.ino'
            sketch_file.write_text(code)
            
            log(f"Sketch creado: {sketch_name}")
            
            # ========================================
            # 5. UPLOAD CON REINTENTOS
            # ========================================
            max_retries = 3
            retry_delays = [0, 500, 1000]  # ms de espera antes de cada intento
            last_result = None
            last_error = None
            
            for attempt in range(max_retries):
                if attempt > 0:
                    delay_ms = retry_delays[attempt]
                    log(f"Reintento {attempt + 1}/{max_retries} después de {delay_ms}ms...")
                    time.sleep(delay_ms / 1000.0)
                
                # ========================================
                # 5.1 RESET DTR/RTS ANTES DE UPLOAD
                # ========================================
                # Forzar reset del Arduino para que entre en modo bootloader
                # Esto mejora la tasa de éxito en uploads repetidos
                log(f"Ejecutando reset DTR/RTS antes del upload (intento {attempt + 1})")
                reset_ok, reset_msg = reset_arduino_dtr(port, log)
                if not reset_ok:
                    log(f"Advertencia: reset DTR falló: {reset_msg} (continuando de todos modos)")
                    # No abortamos, algunos sistemas funcionan sin el reset previo
                
                log(f"Ejecutando arduino-cli compile --upload (intento {attempt + 1})")
                
                try:
                    result = subprocess.run(
                        [
                            ARDUINO_CLI, 'compile', '--upload',
                            '--fqbn', board,
                            '--port', port,
                            '--verbose',  # Más información de debug
                            str(sketch_path)
                        ],
                        capture_output=True,
                        text=True,
                        timeout=180,
                        env=ARDUINO_ENV
                    )
                    
                    last_result = result
                    
                    # Capturar stdout y stderr completos
                    stdout_lines = result.stdout.strip().split('\n') if result.stdout else []
                    stderr_lines = result.stderr.strip().split('\n') if result.stderr else []
                    
                    for line in stdout_lines[-20:]:  # Últimas 20 líneas de stdout
                        if line.strip():
                            logs.append(f"[stdout] {line}")
                    
                    for line in stderr_lines[-20:]:  # Últimas 20 líneas de stderr
                        if line.strip():
                            logs.append(f"[stderr] {line}")
                    
                    if result.returncode == 0:
                        log("Upload exitoso!")
                        response_data = {
                            'ok': True,
                            'success': True,  # Compatibilidad con código existente
                            'message': 'Código subido exitosamente',
                            'details': {'port': port, 'fqbn': board},
                            'logs': logs,
                            'output': result.stdout
                        }
                        # Incluir advertencias y sugerencias si existen
                        if warning_message:
                            response_data['warning'] = warning_message
                        if suggested_board_change:
                            response_data['suggested_board'] = suggested_board_change
                        if device_detection:
                            response_data['device_info'] = device_detection
                        return JsonResponse(response_data)
                    
                    # Analizar el error
                    error_output = result.stderr + result.stdout
                    
                    # Detectar error de sincronización (reintentar)
                    sync_errors = [
                        'sync', 'not in sync', 'programmer is not responding',
                        'stk500', 'avrdude', 'timeout', 'can\'t open device'
                    ]
                    
                    is_sync_error = any(err in error_output.lower() for err in sync_errors)
                    
                    if is_sync_error and attempt < max_retries - 1:
                        log(f"Error de sincronización detectado, reintentando...")
                        last_error = error_output
                        continue
                    else:
                        # Error no recuperable o último intento
                        last_error = error_output
                        break
                        
                except subprocess.TimeoutExpired:
                    log(f"Timeout en intento {attempt + 1}")
                    last_error = "Timeout de subida (180s)"
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return JsonResponse({
                            'ok': False,
                            'error_code': 'UPLOAD_TIMEOUT',
                            'error': 'Timeout de subida',
                            'details': {'port': port, 'fqbn': board},
                            'logs': logs
                        }, status=408)
            
            # ========================================
            # 6. TODOS LOS REINTENTOS FALLARON
            # ========================================
            error_output = last_error or "Error desconocido"
            
            # Determinar el código de error
            error_code = 'UPLOAD_FAIL'
            if 'sync' in error_output.lower() or 'not in sync' in error_output.lower():
                error_code = 'UPLOAD_SYNC_FAIL'
            elif 'can\'t open device' in error_output.lower() or 'permission' in error_output.lower():
                error_code = 'PORT_ACCESS_DENIED'
            elif 'no programmer' in error_output.lower():
                error_code = 'NO_PROGRAMMER'
            elif 'compilation' in error_output.lower() or 'error:' in error_output.lower():
                error_code = 'COMPILE_ERROR'
            
            log(f"Upload fallido con error: {error_code}")
            
            return JsonResponse({
                'ok': False,
                'success': False,  # Compatibilidad
                'error_code': error_code,
                'error': error_output[:2000],  # Limitar longitud del error
                'details': {'port': port, 'fqbn': board},
                'logs': logs,
                'output': last_result.stdout if last_result else ''
            }, status=500)
            
        finally:
            # Liberar el lock del puerto
            port_lock.release()
            log("Lock del puerto liberado")
            
    except json.JSONDecodeError:
        return JsonResponse({
            'ok': False,
            'error_code': 'INVALID_JSON',
            'error': 'JSON inválido en la petición',
            'details': {},
            'logs': logs
        }, status=400)
    except FileNotFoundError:
        return JsonResponse({
            'ok': False,
            'error_code': 'CLI_NOT_FOUND',
            'error': 'arduino-cli no encontrado. Verifica la instalación.',
            'details': {},
            'logs': logs
        }, status=500)
    except Exception as e:
        log(f"Error inesperado: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error_code': 'UNEXPECTED_ERROR',
            'error': str(e),
            'details': {},
            'logs': logs
        }, status=500)
    finally:
        # Limpiar sketch temporal
        if sketch_path and sketch_path.exists():
            try:
                shutil.rmtree(sketch_path)
                log("Sketch temporal eliminado")
            except Exception as e:
                log(f"Error eliminando sketch: {e}")


# ============================================
# MONITOR SERIAL
# ============================================

@csrf_exempt
@require_http_methods(["POST"])
def serial_connect(request):
    """Conecta al puerto serial."""
    global serial_connection
    
    try:
        data = json.loads(request.body)
        port = data.get('port', '')
        baudrate = int(data.get('baudrate', 9600))
        
        if not port:
            return JsonResponse({'success': False, 'error': 'No se especificó puerto'}, status=400)
        
        with serial_lock:
            if serial_connection and serial_connection.is_open:
                serial_connection.close()
            
            serial_connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=0.1
            )
            
        return JsonResponse({
            'success': True,
            'message': f'Conectado a {port} @ {baudrate} baud'
        })
        
    except serial.SerialException as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def serial_disconnect(request):
    """Desconecta del puerto serial."""
    global serial_connection
    
    try:
        with serial_lock:
            if serial_connection and serial_connection.is_open:
                serial_connection.close()
                serial_connection = None
                
        return JsonResponse({'success': True, 'message': 'Desconectado'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def serial_read(request):
    """Lee datos del puerto serial."""
    global serial_connection
    
    try:
        with serial_lock:
            if not serial_connection or not serial_connection.is_open:
                return JsonResponse({'success': False, 'error': 'No hay conexión serial'}, status=400)
            
            data = ''
            if serial_connection.in_waiting > 0:
                raw_data = serial_connection.read(serial_connection.in_waiting)
                data = raw_data.decode('utf-8', errors='replace')
                
        return JsonResponse({'success': True, 'data': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def serial_write(request):
    """Escribe datos al puerto serial."""
    global serial_connection
    
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        newline = data.get('newline', True)
        
        if newline:
            message += '\n'
        
        with serial_lock:
            if not serial_connection or not serial_connection.is_open:
                return JsonResponse({'success': False, 'error': 'No hay conexión serial'}, status=400)
            
            serial_connection.write(message.encode('utf-8'))
            
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def serial_status(request):
    """Obtiene el estado de la conexión serial."""
    global serial_connection
    
    with serial_lock:
        connected = serial_connection is not None and serial_connection.is_open
        port = serial_connection.port if connected else None
        baudrate = serial_connection.baudrate if connected else None
        
    return JsonResponse({
        'connected': connected,
        'port': port,
        'baudrate': baudrate
    })
