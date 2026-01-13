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

# Conexión serial global
serial_connection = None
serial_lock = threading.Lock()


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
            timeout=10
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
            timeout=120
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
            timeout=120
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
    """Compila y sube el código a la placa Arduino."""
    global serial_connection
    sketch_path = None
    
    # Cerrar conexión serial si está abierta
    with serial_lock:
        if serial_connection and serial_connection.is_open:
            serial_connection.close()
            serial_connection = None
    
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        port = data.get('port', '')
        board = data.get('board', 'arduino:avr:uno')
        
        if not code:
            return JsonResponse({'success': False, 'error': 'No code provided'}, status=400)
        if not port:
            return JsonResponse({'success': False, 'error': 'No se especificó puerto'}, status=400)
        
        # Crear directorio único para el sketch
        sketch_id = str(uuid.uuid4())[:8]
        sketch_name = f'sketch_{sketch_id}'
        sketch_path = SKETCH_DIR / sketch_name
        sketch_path.mkdir(exist_ok=True)
        sketch_file = sketch_path / f'{sketch_name}.ino'
        
        # Escribir el código
        sketch_file.write_text(code)
        
        # Compilar y subir usando arduino-cli nativo
        result = subprocess.run(
            [
                ARDUINO_CLI, 'compile', '--upload',
                '--fqbn', board,
                '--port', port,
                str(sketch_path)
            ],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode == 0:
            return JsonResponse({
                'success': True,
                'message': 'Código subido exitosamente',
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
        return JsonResponse({'success': False, 'error': 'Timeout de subida'}, status=408)
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
