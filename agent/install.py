#!/usr/bin/env python3
"""
MAX-IDE Agent - Instalador Universal
Detecta el sistema operativo e instala/configura el Agent automáticamente.

Uso:
    python install.py [--no-autostart] [--uninstall]
"""

import os
import sys
import platform
import subprocess
import shutil
import argparse
import urllib.request
import zipfile
import tarfile
from pathlib import Path

# ============================================
# CONFIGURACIÓN
# ============================================

AGENT_NAME = "MAX-IDE Agent"
AGENT_VERSION = "1.1.0"
AGENT_PORT = 8765

# URLs de arduino-cli (actualizar según versión)
ARDUINO_CLI_VERSION = "0.35.3"
ARDUINO_CLI_URLS = {
    "Linux-x86_64": f"https://github.com/arduino/arduino-cli/releases/download/v{ARDUINO_CLI_VERSION}/arduino-cli_{ARDUINO_CLI_VERSION}_Linux_64bit.tar.gz",
    "Linux-aarch64": f"https://github.com/arduino/arduino-cli/releases/download/v{ARDUINO_CLI_VERSION}/arduino-cli_{ARDUINO_CLI_VERSION}_Linux_ARM64.tar.gz",
    "Darwin-x86_64": f"https://github.com/arduino/arduino-cli/releases/download/v{ARDUINO_CLI_VERSION}/arduino-cli_{ARDUINO_CLI_VERSION}_macOS_64bit.tar.gz",
    "Darwin-arm64": f"https://github.com/arduino/arduino-cli/releases/download/v{ARDUINO_CLI_VERSION}/arduino-cli_{ARDUINO_CLI_VERSION}_macOS_ARM64.tar.gz",
    "Windows-AMD64": f"https://github.com/arduino/arduino-cli/releases/download/v{ARDUINO_CLI_VERSION}/arduino-cli_{ARDUINO_CLI_VERSION}_Windows_64bit.zip",
}

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def color(text, c):
    """Aplica color al texto si la terminal lo soporta."""
    if sys.platform == 'win32':
        return text
    return f"{c}{text}{Colors.END}"

def print_header():
    """Imprime cabecera del instalador."""
    print()
    print(color("=" * 55, Colors.BLUE))
    print(color(f"  {AGENT_NAME} - Instalador v{AGENT_VERSION}", Colors.BOLD))
    print(color("=" * 55, Colors.BLUE))
    print()

def print_step(msg):
    print(color(f"→ {msg}", Colors.BLUE))

def print_ok(msg):
    print(color(f"  ✓ {msg}", Colors.GREEN))

def print_warn(msg):
    print(color(f"  ⚠ {msg}", Colors.YELLOW))

def print_error(msg):
    print(color(f"  ✗ {msg}", Colors.RED))

# ============================================
# DETECCIÓN DE SISTEMA
# ============================================

def get_system_info():
    """Obtiene información del sistema."""
    system = platform.system()
    machine = platform.machine()
    
    # Normalizar arquitectura
    if machine in ['x86_64', 'AMD64']:
        arch = 'x86_64' if system != 'Windows' else 'AMD64'
    elif machine in ['aarch64', 'arm64']:
        arch = 'aarch64' if system == 'Linux' else 'arm64'
    else:
        arch = machine
    
    return {
        'system': system,
        'machine': arch,
        'key': f"{system}-{arch}",
        'is_linux': system == 'Linux',
        'is_mac': system == 'Darwin',
        'is_windows': system == 'Windows',
    }

def get_install_dir():
    """Obtiene el directorio de instalación."""
    if platform.system() == 'Windows':
        return Path(os.environ.get('LOCALAPPDATA', '~')) / 'MAX-IDE-Agent'
    elif platform.system() == 'Darwin':
        return Path.home() / 'Library' / 'Application Support' / 'MAX-IDE-Agent'
    else:
        return Path.home() / '.local' / 'share' / 'maxide-agent'

def get_bin_dir():
    """Obtiene el directorio de binarios del usuario."""
    if platform.system() == 'Windows':
        return get_install_dir() / 'bin'
    elif platform.system() == 'Darwin':
        return Path.home() / '.local' / 'bin'
    else:
        return Path.home() / '.local' / 'bin'

# ============================================
# BÚSQUEDA DE ARDUINO-CLI
# ============================================

def find_arduino_cli():
    """Busca arduino-cli en el sistema."""
    possible_paths = []
    
    system = platform.system()
    
    if system == 'Linux':
        possible_paths = [
            '/usr/local/bin/arduino-cli',
            '/usr/bin/arduino-cli',
            '/snap/bin/arduino-cli',
            Path.home() / '.local' / 'bin' / 'arduino-cli',
            Path.home() / 'bin' / 'arduino-cli',
            # Arduino IDE 2.x en Linux
            Path.home() / '.local' / 'share' / 'arduino-ide' / 'resources' / 'app' / 'lib' / 'backend' / 'resources' / 'arduino-cli',
            Path('/opt/arduino-ide/resources/app/lib/backend/resources/arduino-cli'),
        ]
    elif system == 'Darwin':
        possible_paths = [
            '/usr/local/bin/arduino-cli',
            '/opt/homebrew/bin/arduino-cli',
            Path.home() / '.local' / 'bin' / 'arduino-cli',
            # Arduino IDE 2.x en Mac
            Path('/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli'),
            Path.home() / 'Applications' / 'Arduino IDE.app' / 'Contents' / 'Resources' / 'app' / 'lib' / 'backend' / 'resources' / 'arduino-cli',
        ]
    elif system == 'Windows':
        possible_paths = [
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Arduino15' / 'arduino-cli.exe',
            Path(os.environ.get('PROGRAMFILES', '')) / 'Arduino CLI' / 'arduino-cli.exe',
            Path(os.environ.get('PROGRAMFILES(X86)', '')) / 'Arduino CLI' / 'arduino-cli.exe',
            # Arduino IDE 2.x en Windows
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Arduino IDE' / 'resources' / 'app' / 'lib' / 'backend' / 'resources' / 'arduino-cli.exe',
            Path(os.environ.get('PROGRAMFILES', '')) / 'Arduino IDE' / 'resources' / 'app' / 'lib' / 'backend' / 'resources' / 'arduino-cli.exe',
        ]
    
    # Añadir directorio de instalación del Agent
    install_dir = get_install_dir()
    if system == 'Windows':
        possible_paths.append(install_dir / 'bin' / 'arduino-cli.exe')
    else:
        possible_paths.append(install_dir / 'bin' / 'arduino-cli')
    
    # Buscar en PATH
    which_result = shutil.which('arduino-cli')
    if which_result:
        return Path(which_result)
    
    # Buscar en rutas conocidas
    for path in possible_paths:
        path = Path(path)
        if path.exists() and os.access(str(path), os.X_OK):
            return path
    
    return None

# ============================================
# INSTALACIÓN DE ARDUINO-CLI
# ============================================

def download_arduino_cli(sys_info):
    """Descarga e instala arduino-cli."""
    url = ARDUINO_CLI_URLS.get(sys_info['key'])
    
    if not url:
        print_error(f"No hay descarga disponible para {sys_info['key']}")
        return None
    
    install_dir = get_install_dir()
    bin_dir = install_dir / 'bin'
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    print_step(f"Descargando arduino-cli v{ARDUINO_CLI_VERSION}...")
    
    try:
        # Descargar archivo
        filename = url.split('/')[-1]
        download_path = install_dir / filename
        
        urllib.request.urlretrieve(url, download_path)
        print_ok(f"Descargado: {filename}")
        
        # Extraer
        print_step("Extrayendo arduino-cli...")
        
        if filename.endswith('.zip'):
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(bin_dir)
        elif filename.endswith('.tar.gz'):
            with tarfile.open(download_path, 'r:gz') as tar_ref:
                tar_ref.extractall(bin_dir)
        
        # Buscar el ejecutable
        if sys_info['is_windows']:
            cli_path = bin_dir / 'arduino-cli.exe'
        else:
            cli_path = bin_dir / 'arduino-cli'
            # Hacer ejecutable
            os.chmod(cli_path, 0o755)
        
        # Limpiar archivo descargado
        download_path.unlink()
        
        print_ok(f"arduino-cli instalado en: {cli_path}")
        return cli_path
        
    except Exception as e:
        print_error(f"Error descargando arduino-cli: {e}")
        return None

def setup_arduino_cli(cli_path):
    """Configura arduino-cli (instala cores básicos)."""
    print_step("Configurando arduino-cli...")
    
    try:
        # Actualizar índice
        subprocess.run([str(cli_path), 'core', 'update-index'], 
                      capture_output=True, timeout=60)
        
        # Instalar core de Arduino AVR (UNO, Nano, Mega)
        print_step("Instalando soporte para Arduino AVR...")
        result = subprocess.run(
            [str(cli_path), 'core', 'install', 'arduino:avr'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print_ok("Core arduino:avr instalado")
        else:
            print_warn("No se pudo instalar core AVR (puede que ya esté instalado)")
        
        return True
        
    except subprocess.TimeoutExpired:
        print_warn("Timeout configurando arduino-cli")
        return False
    except Exception as e:
        print_warn(f"Error configurando arduino-cli: {e}")
        return False

# ============================================
# INSTALACIÓN DE DEPENDENCIAS PYTHON
# ============================================

def check_python():
    """Verifica Python y pip."""
    print_step("Verificando Python...")
    
    # Verificar versión
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print_error(f"Python 3.7+ requerido. Tienes: {version.major}.{version.minor}")
        return False
    
    print_ok(f"Python {version.major}.{version.minor}.{version.micro}")
    return True

def install_python_deps():
    """Instala dependencias Python."""
    print_step("Instalando dependencias Python...")
    
    deps = ['flask', 'flask-cors', 'requests', 'pyserial']
    
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--user', '-q'] + deps,
            check=True,
            timeout=120
        )
        print_ok("Dependencias instaladas: " + ", ".join(deps))
        return True
    except Exception as e:
        print_error(f"Error instalando dependencias: {e}")
        return False

# ============================================
# INSTALACIÓN DEL AGENT
# ============================================

def install_agent_files():
    """Copia los archivos del Agent al directorio de instalación."""
    print_step("Instalando archivos del Agent...")
    
    install_dir = get_install_dir()
    install_dir.mkdir(parents=True, exist_ok=True)
    
    # Directorio actual del script (donde está agent.py)
    script_dir = Path(__file__).parent
    agent_file = script_dir / 'agent.py'
    
    if not agent_file.exists():
        print_error("No se encontró agent.py")
        return False
    
    # Copiar archivos
    target_agent = install_dir / 'agent.py'
    shutil.copy2(agent_file, target_agent)
    
    # Copiar requirements si existe
    req_file = script_dir / 'requirements.txt'
    if req_file.exists():
        shutil.copy2(req_file, install_dir / 'requirements.txt')
    
    print_ok(f"Agent instalado en: {install_dir}")
    return True

# ============================================
# CONFIGURACIÓN DE AUTO-START
# ============================================

def setup_autostart_linux():
    """Configura auto-start en Linux con systemd."""
    print_step("Configurando inicio automático (systemd)...")
    
    install_dir = get_install_dir()
    cli_path = find_arduino_cli()
    
    # Crear servicio systemd del usuario
    systemd_dir = Path.home() / '.config' / 'systemd' / 'user'
    systemd_dir.mkdir(parents=True, exist_ok=True)
    
    service_content = f"""[Unit]
Description=MAX-IDE Agent Local
After=network.target

[Service]
Type=simple
WorkingDirectory={install_dir}
ExecStart={sys.executable} {install_dir}/agent.py --port {AGENT_PORT}
Restart=on-failure
RestartSec=10
Environment="PYTHONUNBUFFERED=1"
{f'Environment="ARDUINO_CLI_PATH={cli_path}"' if cli_path else ''}

[Install]
WantedBy=default.target
"""
    
    service_file = systemd_dir / 'maxide-agent.service'
    service_file.write_text(service_content)
    
    # Habilitar servicio
    try:
        subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', '--user', 'enable', 'maxide-agent.service'], check=True)
        subprocess.run(['systemctl', '--user', 'start', 'maxide-agent.service'], check=True)
        # Habilitar lingering para que el servicio inicie sin login
        subprocess.run(['loginctl', 'enable-linger', os.environ.get('USER', '')], capture_output=True)
        print_ok("Servicio systemd configurado y activo")
        return True
    except Exception as e:
        print_warn(f"Error configurando systemd: {e}")
        print_warn("Puedes iniciar manualmente con: systemctl --user start maxide-agent")
        return False

def setup_autostart_mac():
    """Configura auto-start en macOS con launchd."""
    print_step("Configurando inicio automático (launchd)...")
    
    install_dir = get_install_dir()
    cli_path = find_arduino_cli()
    
    # Crear LaunchAgent
    launch_agents_dir = Path.home() / 'Library' / 'LaunchAgents'
    launch_agents_dir.mkdir(parents=True, exist_ok=True)
    
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.maxide.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{install_dir}/agent.py</string>
        <string>--port</string>
        <string>{AGENT_PORT}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{install_dir}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{install_dir}/agent.log</string>
    <key>StandardErrorPath</key>
    <string>{install_dir}/agent.log</string>
    {f'''<key>EnvironmentVariables</key>
    <dict>
        <key>ARDUINO_CLI_PATH</key>
        <string>{cli_path}</string>
    </dict>''' if cli_path else ''}
</dict>
</plist>
"""
    
    plist_file = launch_agents_dir / 'com.maxide.agent.plist'
    plist_file.write_text(plist_content)
    
    # Cargar el servicio
    try:
        subprocess.run(['launchctl', 'unload', str(plist_file)], capture_output=True)
        subprocess.run(['launchctl', 'load', str(plist_file)], check=True)
        print_ok("LaunchAgent configurado y activo")
        return True
    except Exception as e:
        print_warn(f"Error configurando launchd: {e}")
        return False

def setup_autostart_windows():
    """Configura auto-start en Windows."""
    print_step("Configurando inicio automático (Startup)...")
    
    install_dir = get_install_dir()
    cli_path = find_arduino_cli()
    
    # Crear script VBS para inicio silencioso
    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{install_dir}"
WshShell.Run """{sys.executable}"" ""{install_dir}\\agent.py"" --port {AGENT_PORT}", 0, False
'''
    
    vbs_file = install_dir / 'start_agent.vbs'
    vbs_file.write_text(vbs_content)
    
    # Crear acceso directo en Startup
    startup_dir = Path(os.environ.get('APPDATA', '')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
    
    if startup_dir.exists():
        # Crear .bat que ejecuta el .vbs
        bat_content = f'@echo off\nwscript.exe "{vbs_file}"\n'
        bat_file = startup_dir / 'MAX-IDE-Agent.bat'
        bat_file.write_text(bat_content)
        print_ok("Configurado inicio automático en Windows Startup")
        return True
    else:
        print_warn("No se encontró carpeta Startup")
        return False

def setup_autostart(sys_info, skip=False):
    """Configura auto-start según el sistema operativo."""
    if skip:
        print_step("Auto-start omitido (--no-autostart)")
        return True
    
    if sys_info['is_linux']:
        return setup_autostart_linux()
    elif sys_info['is_mac']:
        return setup_autostart_mac()
    elif sys_info['is_windows']:
        return setup_autostart_windows()
    
    return False

# ============================================
# CREAR ACCESO DIRECTO / LAUNCHER
# ============================================

def create_desktop_shortcut(sys_info):
    """Crea acceso directo en el escritorio."""
    print_step("Creando acceso directo...")
    
    install_dir = get_install_dir()
    
    # Detectar escritorio
    desktop = None
    for d in ['Desktop', 'Escritorio', 'Bureau']:
        path = Path.home() / d
        if path.exists():
            desktop = path
            break
    
    if not desktop:
        print_warn("No se encontró carpeta de escritorio")
        return False
    
    if sys_info['is_linux']:
        # Crear .desktop
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=MAX-IDE Agent
Comment=Agente local para subir código a Arduino
Exec={sys.executable} {install_dir}/agent.py --port {AGENT_PORT}
Icon=utilities-terminal
Terminal=false
Categories=Development;Electronics;
StartupNotify=false
"""
        desktop_file = desktop / 'maxide-agent.desktop'
        desktop_file.write_text(desktop_content)
        os.chmod(desktop_file, 0o755)
        
    elif sys_info['is_mac']:
        # Crear AppleScript app
        app_content = f'''do shell script "{sys.executable} {install_dir}/agent.py --port {AGENT_PORT} &"
'''
        # Por simplicidad, crear shell script
        script_file = desktop / 'MAX-IDE Agent.command'
        script_file.write_text(f'#!/bin/bash\n{sys.executable} "{install_dir}/agent.py" --port {AGENT_PORT}\n')
        os.chmod(script_file, 0o755)
        
    elif sys_info['is_windows']:
        # Crear .bat en escritorio
        bat_content = f'@echo off\nstart "" "{sys.executable}" "{install_dir}\\agent.py" --port {AGENT_PORT}\n'
        bat_file = desktop / 'MAX-IDE Agent.bat'
        bat_file.write_text(bat_content)
    
    print_ok(f"Acceso directo creado en: {desktop}")
    return True

# ============================================
# DESINSTALACIÓN
# ============================================

def uninstall(sys_info):
    """Desinstala el Agent."""
    print_step("Desinstalando MAX-IDE Agent...")
    
    # Detener servicio
    if sys_info['is_linux']:
        subprocess.run(['systemctl', '--user', 'stop', 'maxide-agent.service'], capture_output=True)
        subprocess.run(['systemctl', '--user', 'disable', 'maxide-agent.service'], capture_output=True)
        service_file = Path.home() / '.config' / 'systemd' / 'user' / 'maxide-agent.service'
        if service_file.exists():
            service_file.unlink()
            
    elif sys_info['is_mac']:
        plist_file = Path.home() / 'Library' / 'LaunchAgents' / 'com.maxide.agent.plist'
        subprocess.run(['launchctl', 'unload', str(plist_file)], capture_output=True)
        if plist_file.exists():
            plist_file.unlink()
            
    elif sys_info['is_windows']:
        startup_file = Path(os.environ.get('APPDATA', '')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup' / 'MAX-IDE-Agent.bat'
        if startup_file.exists():
            startup_file.unlink()
    
    # Eliminar directorio de instalación
    install_dir = get_install_dir()
    if install_dir.exists():
        shutil.rmtree(install_dir)
        print_ok(f"Eliminado: {install_dir}")
    
    # Eliminar acceso directo
    for d in ['Desktop', 'Escritorio', 'Bureau']:
        desktop = Path.home() / d
        if desktop.exists():
            for f in desktop.glob('*maxide*'):
                f.unlink()
            for f in desktop.glob('*MAX-IDE*'):
                f.unlink()
    
    print_ok("MAX-IDE Agent desinstalado")
    return True

# ============================================
# MAIN
# ============================================

def main():
    parser = argparse.ArgumentParser(description=f'{AGENT_NAME} - Instalador')
    parser.add_argument('--no-autostart', action='store_true',
                        help='No configurar inicio automático')
    parser.add_argument('--uninstall', action='store_true',
                        help='Desinstalar el Agent')
    parser.add_argument('--skip-arduino-cli', action='store_true',
                        help='No instalar arduino-cli')
    
    args = parser.parse_args()
    
    print_header()
    
    # Obtener info del sistema
    sys_info = get_system_info()
    print(f"Sistema: {sys_info['system']} ({sys_info['machine']})")
    print()
    
    # Desinstalar?
    if args.uninstall:
        uninstall(sys_info)
        return 0
    
    # ========================================
    # 1. VERIFICAR PYTHON
    # ========================================
    if not check_python():
        return 1
    
    # ========================================
    # 2. INSTALAR DEPENDENCIAS PYTHON
    # ========================================
    if not install_python_deps():
        print_warn("Continuando sin algunas dependencias...")
    
    # ========================================
    # 3. BUSCAR/INSTALAR ARDUINO-CLI
    # ========================================
    print_step("Buscando arduino-cli...")
    cli_path = find_arduino_cli()
    
    if cli_path:
        print_ok(f"arduino-cli encontrado: {cli_path}")
    elif not args.skip_arduino_cli:
        print_warn("arduino-cli no encontrado")
        
        response = input("\n¿Deseas descargar e instalar arduino-cli? [S/n]: ").strip().lower()
        if response != 'n':
            cli_path = download_arduino_cli(sys_info)
            if cli_path:
                setup_arduino_cli(cli_path)
    else:
        print_warn("arduino-cli no encontrado (omitido)")
    
    # ========================================
    # 4. INSTALAR ARCHIVOS DEL AGENT
    # ========================================
    if not install_agent_files():
        return 1
    
    # ========================================
    # 5. CONFIGURAR AUTO-START
    # ========================================
    setup_autostart(sys_info, skip=args.no_autostart)
    
    # ========================================
    # 6. CREAR ACCESO DIRECTO
    # ========================================
    create_desktop_shortcut(sys_info)
    
    # ========================================
    # RESUMEN FINAL
    # ========================================
    print()
    print(color("=" * 55, Colors.GREEN))
    print(color("  ✓ Instalación completada", Colors.GREEN + Colors.BOLD))
    print(color("=" * 55, Colors.GREEN))
    print()
    
    install_dir = get_install_dir()
    print(f"  Directorio: {install_dir}")
    print(f"  Puerto: http://localhost:{AGENT_PORT}")
    if cli_path:
        print(f"  arduino-cli: {cli_path}")
    print()
    
    if args.no_autostart:
        print("  Para iniciar manualmente:")
        print(f"    python {install_dir}/agent.py")
    else:
        print("  El Agent se iniciará automáticamente con el sistema.")
        print("  También puedes usar el acceso directo en el escritorio.")
    
    print()
    print("  Ahora puedes abrir MAX-IDE en tu navegador y subir código!")
    print()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

