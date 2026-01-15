import json
import os
import subprocess
import shutil
import uuid
import threading
import re
import base64
import time
from pathlib import Path

from django.http import JsonResponse
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
    if not ports:
        try:
            for port in serial.tools.list_ports.comports():
                ports.append({
                    'device': port.device,
                    'description': port.description or 'Puerto Serial',
                    'protocol': 'serial',
                    'board_name': '',
                    'board_fqbn': '',
                    'hwid': port.hwid or ''
                })
        except Exception:
            pass
    
    return JsonResponse({'ports': ports})


@csrf_exempt
@require_http_methods(["POST"])
def compile_code(request):
    """Compila el código Arduino."""
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
        
        # Compilar usando arduino-cli nativo
        result = subprocess.run(
            [ARDUINO_CLI, 'compile', '--fqbn', board, str(sketch_path)],
            capture_output=True,
            text=True,
            timeout=120,
            env=ARDUINO_ENV
        )
        
        if result.returncode == 0:
            return JsonResponse({
                'success': True,
                'message': 'Compilación exitosa',
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
                        return JsonResponse({
                            'ok': True,
                            'success': True,  # Compatibilidad con código existente
                            'message': 'Código subido exitosamente',
                            'details': {'port': port, 'fqbn': board},
                            'logs': logs,
                            'output': result.stdout
                        })
                    
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
