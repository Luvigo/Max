/**
 * MAX-IDE - Aplicación principal
 * Arduino Block Editor con Blockly
 */

// ============================================
// CONFIGURACIÓN GLOBAL
// ============================================

let workspace = null;
let currentPort = '';
let currentBoard = 'arduino:avr:uno';
let serialReadInterval = null;
let isSerialConnected = false;
let portCheckInterval = null;
let lastKnownPorts = [];

// ============================================
// TEMA PERSONALIZADO DE BLOCKLY
// ============================================

const darkTheme = Blockly.Theme.defineTheme('darkArduino', {
    'base': Blockly.Themes.Classic,
    'componentStyles': {
        'workspaceBackgroundColour': '#0a0e14',
        'toolboxBackgroundColour': '#0d1117',
        'toolboxForegroundColour': '#ffffff',
        'flyoutBackgroundColour': '#151b23',
        'flyoutForegroundColour': '#e6edf3',
        'flyoutOpacity': 1,
        'scrollbarColour': '#3b4555',
        'insertionMarkerColour': '#00d9ff',
        'insertionMarkerOpacity': 0.3,
        'scrollbarOpacity': 0.8,
        'cursorColour': '#00d9ff',
    },
    'categoryStyles': {
        'structure_category': { 'colour': '#f59e0b' },
        'digital_category': { 'colour': '#3b82f6' },
        'analog_category': { 'colour': '#06b6d4' },
        'time_category': { 'colour': '#ec4899' },
        'serial_category': { 'colour': '#ef4444' },
        'control_category': { 'colour': '#8b5cf6' },
        'logic_category': { 'colour': '#6366f1' },
        'math_category': { 'colour': '#10b981' },
        'variable_category': { 'colour': '#f97316' },
        'text_category': { 'colour': '#14b8a6' },
        'component_category': { 'colour': '#eab308' },
        'advanced_category': { 'colour': '#6b7280' },
    },
    'fontStyle': {
        'family': 'Outfit, sans-serif',
        'weight': '500',
        'size': 12
    },
    'startHats': true
});

// ============================================
// INICIALIZACIÓN
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    initBlockly();
    initEventListeners();
    refreshPorts();
    startPortMonitoring();
    logToConsole('MAX-IDE inicializado correctamente', 'success');
});

/**
 * Inicializa el workspace de Blockly
 */
function initBlockly() {
    const toolbox = document.getElementById('toolbox');
    const blocklyDiv = document.getElementById('blocklyDiv');
    
    workspace = Blockly.inject(blocklyDiv, {
        toolbox: toolbox,
        theme: darkTheme,
        grid: {
            spacing: 25,
            length: 3,
            colour: '#1e2530',
            snap: true
        },
        zoom: {
            controls: true,
            wheel: true,
            startScale: 1.0,
            maxScale: 3,
            minScale: 0.3,
            scaleSpeed: 1.2
        },
        trashcan: true,
        move: {
            scrollbars: true,
            drag: true,
            wheel: true
        },
        renderer: 'zelos'
    });
    
    // Listener para cambios
    workspace.addChangeListener(function(event) {
        if (event.type === Blockly.Events.BLOCK_CHANGE ||
            event.type === Blockly.Events.BLOCK_CREATE ||
            event.type === Blockly.Events.BLOCK_DELETE ||
            event.type === Blockly.Events.BLOCK_MOVE) {
            updateCode();
            updateBlockCount();
        }
    });
    
    addInitialBlocks();
    
    window.addEventListener('resize', function() {
        Blockly.svgResize(workspace);
    });
    
    // Aplicar estilos adicionales después de inyectar
    setTimeout(applyCustomStyles, 100);
}

/**
 * Aplica estilos personalizados al toolbox
 */
function applyCustomStyles() {
    // Forzar fondo negro en el toolbox
    const toolbox = document.querySelector('.blocklyToolboxDiv');
    if (toolbox) {
        toolbox.style.backgroundColor = '#0d1117';
        toolbox.style.borderRight = '2px solid #1e2530';
    }
    
    // Estilizar las filas del árbol
    const treeRows = document.querySelectorAll('.blocklyTreeRow');
    treeRows.forEach(row => {
        row.style.backgroundColor = 'transparent';
    });
    
    // Estilizar etiquetas
    const labels = document.querySelectorAll('.blocklyTreeLabel');
    labels.forEach(label => {
        label.style.color = '#ffffff';
        label.style.fontFamily = 'Outfit, sans-serif';
        label.style.fontSize = '14px';
        label.style.fontWeight = '600';
    });
}

/**
 * Añade bloques iniciales al workspace
 */
function addInitialBlocks() {
    const xml = `
        <xml>
            <block type="arduino_setup" x="50" y="50">
                <statement name="SETUP_CODE">
                    <block type="arduino_pin_mode">
                        <field name="PIN">13</field>
                        <field name="MODE">OUTPUT</field>
                        <next>
                            <block type="arduino_serial_begin">
                                <field name="BAUD">9600</field>
                            </block>
                        </next>
                    </block>
                </statement>
            </block>
            <block type="arduino_loop" x="50" y="220">
                <statement name="LOOP_CODE">
                    <block type="arduino_digital_write">
                        <field name="PIN">13</field>
                        <field name="VALUE">HIGH</field>
                        <next>
                            <block type="arduino_delay">
                                <value name="TIME">
                                    <block type="arduino_number">
                                        <field name="NUM">1000</field>
                                    </block>
                                </value>
                                <next>
                                    <block type="arduino_digital_write">
                                        <field name="PIN">13</field>
                                        <field name="VALUE">LOW</field>
                                        <next>
                                            <block type="arduino_delay">
                                                <value name="TIME">
                                                    <block type="arduino_number">
                                                        <field name="NUM">1000</field>
                                                    </block>
                                                </value>
                                            </block>
                                        </next>
                                    </block>
                                </next>
                            </block>
                        </next>
                    </block>
                </statement>
            </block>
        </xml>
    `;
    
    const dom = Blockly.utils.xml.textToDom(xml);
    Blockly.Xml.domToWorkspace(dom, workspace);
    updateCode();
}

/**
 * Inicializa los event listeners
 */
function initEventListeners() {
    // Botones principales
    document.getElementById('btnCompile').addEventListener('click', compileCode);
    document.getElementById('btnUpload').addEventListener('click', uploadCode);
    document.getElementById('btnRefreshPorts').addEventListener('click', refreshPorts);
    
    // Botones de archivo
    document.getElementById('btnNew').addEventListener('click', newProject);
    document.getElementById('btnSave').addEventListener('click', saveProject);
    document.getElementById('btnLoad').addEventListener('click', () => document.getElementById('fileInput').click());
    document.getElementById('fileInput').addEventListener('change', loadProject);
    
    // Otros botones
    document.getElementById('btnCopyCode').addEventListener('click', copyCode);
    document.getElementById('btnClearConsole').addEventListener('click', clearConsole);
    
    // Selectores
    document.getElementById('portSelect').addEventListener('change', function(e) {
        currentPort = e.target.value;
        updateConnectionStatus();
        if (currentPort) {
            logToConsole(`Puerto seleccionado: ${currentPort}`, 'info');
        }
    });
    
    document.getElementById('boardSelect').addEventListener('change', function(e) {
        currentBoard = e.target.value;
        const boardNames = {
            'arduino:avr:uno': 'Arduino UNO',
            'arduino:avr:nano': 'Arduino Nano',
            'arduino:avr:mega': 'Arduino Mega',
            'arduino:avr:leonardo': 'Arduino Leonardo'
        };
        document.getElementById('boardInfo').innerHTML = `<span>🎯</span><span>${boardNames[currentBoard]}</span>`;
        logToConsole(`Placa seleccionada: ${boardNames[currentBoard]}`, 'info');
    });
    
    // Monitor Serial
    document.getElementById('btnSerialMonitor').addEventListener('click', openSerialMonitor);
    document.getElementById('btnCloseSerial').addEventListener('click', closeSerialMonitor);
    document.getElementById('btnSerialConnect').addEventListener('click', connectSerial);
    document.getElementById('btnSerialDisconnect').addEventListener('click', disconnectSerial);
    document.getElementById('btnSerialSend').addEventListener('click', sendSerialData);
    document.getElementById('btnClearSerial').addEventListener('click', clearSerialOutput);
    
    document.getElementById('serialInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendSerialData();
    });
    
    document.getElementById('serialModal').addEventListener('click', function(e) {
        if (e.target === this) closeSerialMonitor();
    });
    
    // Atajos de teclado
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 's': e.preventDefault(); saveProject(); break;
                case 'u': e.preventDefault(); uploadCode(); break;
                case 'r': e.preventDefault(); compileCode(); break;
            }
        }
    });
}

// ============================================
// MONITOREO AUTOMÁTICO DE PUERTOS
// ============================================

/**
 * Inicia el monitoreo de puertos
 */
function startPortMonitoring() {
    // Verificar puertos cada 2 segundos
    portCheckInterval = setInterval(checkForNewPorts, 2000);
}

/**
 * Verifica si hay nuevos puertos conectados
 */
async function checkForNewPorts() {
    try {
        const response = await fetch('/api/ports/');
        const data = await response.json();
        const currentPorts = data.ports || [];
        
        // Detectar nuevos puertos
        const newPorts = currentPorts.filter(p => 
            !lastKnownPorts.find(lp => lp.device === p.device)
        );
        
        // Detectar puertos desconectados
        const removedPorts = lastKnownPorts.filter(lp => 
            !currentPorts.find(p => p.device === lp.device)
        );
        
        // Si hay un nuevo puerto Arduino
        if (newPorts.length > 0) {
            const arduinoPort = newPorts.find(p => 
                p.description.toLowerCase().includes('arduino') ||
                p.description.toLowerCase().includes('ch340') ||
                p.description.toLowerCase().includes('cp210') ||
                p.description.toLowerCase().includes('ftdi') ||
                p.description.toLowerCase().includes('usb') ||
                p.device.includes('ttyUSB') ||
                p.device.includes('ttyACM')
            );
            
            if (arduinoPort) {
                await refreshPorts();
                autoSelectPort(arduinoPort);
                detectBoard(arduinoPort);
                showToast(`Arduino conectado en ${arduinoPort.device}`, 'success');
                logToConsole(`🔌 Arduino detectado: ${arduinoPort.device}`, 'success');
            }
        }
        
        // Si se desconectó un puerto
        if (removedPorts.length > 0) {
            removedPorts.forEach(port => {
                if (port.device === currentPort) {
                    currentPort = '';
                    updateConnectionStatus();
                    showToast(`Arduino desconectado de ${port.device}`, 'warning');
                    logToConsole(`⚠️ Arduino desconectado: ${port.device}`, 'warning');
                }
            });
            await refreshPorts();
        }
        
        lastKnownPorts = currentPorts;
        
    } catch (error) {
        // Silenciar errores de polling
    }
}

/**
 * Auto-selecciona un puerto
 */
function autoSelectPort(port) {
    const select = document.getElementById('portSelect');
    const serialSelect = document.getElementById('serialPortSelect');
    
    select.value = port.device;
    if (serialSelect) serialSelect.value = port.device;
    
    currentPort = port.device;
    updateConnectionStatus();
}

/**
 * Detecta el tipo de placa
 */
function detectBoard(port) {
    const boardSelect = document.getElementById('boardSelect');
    
    // Si arduino-cli detectó la placa automáticamente
    if (port.board_fqbn) {
        const fqbn = port.board_fqbn;
        const boardName = port.board_name || 'Arduino';
        
        // Verificar si el FQBN está en nuestras opciones
        const option = boardSelect.querySelector(`option[value="${fqbn}"]`);
        if (option) {
            boardSelect.value = fqbn;
            currentBoard = fqbn;
        } else {
            // Agregar la opción si no existe
            const newOption = document.createElement('option');
            newOption.value = fqbn;
            newOption.textContent = boardName;
            boardSelect.appendChild(newOption);
            boardSelect.value = fqbn;
            currentBoard = fqbn;
        }
        
        document.getElementById('boardInfo').innerHTML = `<span>🎯</span><span>${boardName}</span>`;
        logToConsole(`Placa detectada: ${boardName}`, 'success');
        return;
    }
    
    // Fallback: detectar por descripción
    const desc = (port.description || '').toLowerCase();
    
    if (desc.includes('mega')) {
        boardSelect.value = 'arduino:avr:mega';
        currentBoard = 'arduino:avr:mega';
        document.getElementById('boardInfo').innerHTML = '<span>🎯</span><span>Arduino Mega</span>';
    } else if (desc.includes('nano')) {
        boardSelect.value = 'arduino:avr:nano';
        currentBoard = 'arduino:avr:nano';
        document.getElementById('boardInfo').innerHTML = '<span>🎯</span><span>Arduino Nano</span>';
    } else if (desc.includes('leonardo')) {
        boardSelect.value = 'arduino:avr:leonardo';
        currentBoard = 'arduino:avr:leonardo';
        document.getElementById('boardInfo').innerHTML = '<span>🎯</span><span>Arduino Leonardo</span>';
    } else {
        boardSelect.value = 'arduino:avr:uno';
        currentBoard = 'arduino:avr:uno';
        document.getElementById('boardInfo').innerHTML = '<span>🎯</span><span>Arduino UNO</span>';
    }
}

// ============================================
// GENERACIÓN DE CÓDIGO
// ============================================

function updateCode() {
    try {
        const code = arduinoGenerator.workspaceToCode(workspace);
        document.getElementById('codeOutput').textContent = code || getEmptyCode();
    } catch (error) {
        console.error('Error generating code:', error);
    }
}

function getEmptyCode() {
    return `// Arrastra bloques para generar código

void setup() {
  
}

void loop() {
  
}`;
}

// ============================================
// COMUNICACIÓN CON ARDUINO
// ============================================

async function refreshPorts() {
    const select = document.getElementById('portSelect');
    const serialSelect = document.getElementById('serialPortSelect');
    const btn = document.getElementById('btnRefreshPorts');
    
    btn.innerHTML = '<span class="loading"></span>';
    
    try {
        const response = await fetch('/api/ports/');
        const data = await response.json();
        
        const ports = data.ports || [];
        lastKnownPorts = ports;
        
        const optionsHtml = '<option value="">Seleccionar...</option>' +
            ports.map(port => 
                `<option value="${port.device}">${port.device} - ${port.description}</option>`
            ).join('');
        
        select.innerHTML = optionsHtml;
        if (serialSelect) serialSelect.innerHTML = optionsHtml;
        
        // Auto-seleccionar si hay un Arduino
        if (ports.length > 0 && !currentPort) {
            const arduinoPort = ports.find(p => 
                p.description.toLowerCase().includes('arduino') ||
                p.description.toLowerCase().includes('ch340') ||
                p.description.toLowerCase().includes('cp210') ||
                p.device.includes('ttyUSB') ||
                p.device.includes('ttyACM')
            );
            
            if (arduinoPort) {
                autoSelectPort(arduinoPort);
                detectBoard(arduinoPort);
            }
        }
        
        // Mantener selección actual si sigue disponible
        if (currentPort && ports.find(p => p.device === currentPort)) {
            select.value = currentPort;
            if (serialSelect) serialSelect.value = currentPort;
        }
        
        if (ports.length > 0) {
            logToConsole(`${ports.length} puerto(s) disponible(s)`, 'success');
        } else {
            logToConsole('No se encontraron puertos', 'warning');
        }
        
    } catch (error) {
        logToConsole('Error al buscar puertos: ' + error.message, 'error');
    }
    
    btn.innerHTML = '🔄';
}

function updateConnectionStatus() {
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('statusText');
    
    if (currentPort) {
        dot.classList.remove('disconnected');
        text.textContent = `Conectado: ${currentPort}`;
    } else {
        dot.classList.add('disconnected');
        text.textContent = 'Sin conexión';
    }
}

async function compileCode() {
    const btn = document.getElementById('btnCompile');
    const code = arduinoGenerator.workspaceToCode(workspace);
    
    if (!code.trim()) {
        showToast('No hay código para compilar', 'warning');
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> Verificando...';
    logToConsole('Iniciando verificación...', 'info');
    
    try {
        const response = await fetch('/api/compile/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, board: currentBoard })
        });
        
        const data = await response.json();
        
        if (data.success) {
            logToConsole('✓ Verificación exitosa', 'success');
            if (data.output) {
                data.output.split('\n').filter(l => l.trim()).forEach(line => 
                    logToConsole(line, 'info')
                );
            }
            showToast('Verificación exitosa', 'success');
        } else {
            logToConsole('✗ Error de verificación:', 'error');
            logToConsole(data.error || 'Error desconocido', 'error');
            showToast('Error de verificación', 'error');
        }
    } catch (error) {
        logToConsole('Error: ' + error.message, 'error');
        showToast('Error de conexión', 'error');
    }
    
    btn.disabled = false;
    btn.innerHTML = '<span>⚙️</span><span>Verificar</span>';
}

async function uploadCode() {
    const btn = document.getElementById('btnUpload');
    const code = arduinoGenerator.workspaceToCode(workspace);
    
    if (!code.trim()) {
        showToast('No hay código para subir', 'warning');
        return;
    }
    
    if (!currentPort) {
        showToast('Selecciona un puerto primero', 'warning');
        return;
    }
    
    if (isSerialConnected) {
        await disconnectSerial();
    }
    
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> Subiendo...';
    logToConsole(`Subiendo a ${currentPort}...`, 'info');
    
    try {
        const response = await fetch('/api/upload/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, port: currentPort, board: currentBoard })
        });
        
        const data = await response.json();
        
        if (data.success) {
            logToConsole('✓ ¡Código subido exitosamente!', 'success');
            if (data.output) {
                data.output.split('\n').filter(l => l.trim()).forEach(line => 
                    logToConsole(line, 'info')
                );
            }
            showToast('¡Código subido exitosamente!', 'success');
        } else {
            logToConsole('✗ Error al subir:', 'error');
            logToConsole(data.error || 'Error desconocido', 'error');
            showToast('Error al subir código', 'error');
        }
    } catch (error) {
        logToConsole('Error: ' + error.message, 'error');
        showToast('Error de conexión', 'error');
    }
    
    btn.disabled = false;
    btn.innerHTML = '<span>🚀</span><span>Subir</span>';
}

// ============================================
// MONITOR SERIAL
// ============================================

function openSerialMonitor() {
    document.getElementById('serialModal').classList.add('active');
    refreshPorts();
}

function closeSerialMonitor() {
    document.getElementById('serialModal').classList.remove('active');
}

async function connectSerial() {
    const port = document.getElementById('serialPortSelect').value;
    const baudrate = document.getElementById('serialBaudrate').value;
    
    if (!port) {
        showToast('Selecciona un puerto', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/serial/connect/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ port, baudrate: parseInt(baudrate) })
        });
        
        const data = await response.json();
        
        if (data.success) {
            isSerialConnected = true;
            updateSerialUI(true, port, baudrate);
            addSerialLine(`Conectado a ${port} @ ${baudrate} baud`, 'system');
            serialReadInterval = setInterval(readSerialData, 100);
            showToast('Monitor serial conectado', 'success');
        } else {
            showToast(data.error || 'Error al conectar', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function disconnectSerial() {
    try {
        if (serialReadInterval) {
            clearInterval(serialReadInterval);
            serialReadInterval = null;
        }
        
        await fetch('/api/serial/disconnect/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        isSerialConnected = false;
        updateSerialUI(false);
        addSerialLine('Desconectado', 'system');
    } catch (error) {
        console.error('Error:', error);
    }
}

async function readSerialData() {
    if (!isSerialConnected) return;
    
    try {
        const response = await fetch('/api/serial/read/');
        const data = await response.json();
        
        if (data.success && data.data) {
            data.data.split('\n').forEach(line => {
                if (line.trim()) addSerialLine(line, 'received');
            });
        }
    } catch (error) {}
}

async function sendSerialData() {
    if (!isSerialConnected) return;
    
    const input = document.getElementById('serialInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    try {
        const response = await fetch('/api/serial/write/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, newline: true })
        });
        
        const data = await response.json();
        
        if (data.success) {
            addSerialLine(`> ${message}`, 'sent');
            input.value = '';
        }
    } catch (error) {
        showToast('Error al enviar', 'error');
    }
}

function updateSerialUI(connected, port = '', baudrate = '') {
    const connectBtn = document.getElementById('btnSerialConnect');
    const disconnectBtn = document.getElementById('btnSerialDisconnect');
    const status = document.getElementById('serialStatus');
    const input = document.getElementById('serialInput');
    const sendBtn = document.getElementById('btnSerialSend');
    
    if (connected) {
        connectBtn.classList.add('hidden');
        disconnectBtn.classList.remove('hidden');
        status.className = 'connection-status connected';
        status.innerHTML = `<span class="status-dot"></span><span>${port} @ ${baudrate}</span>`;
        input.disabled = false;
        sendBtn.disabled = false;
    } else {
        connectBtn.classList.remove('hidden');
        disconnectBtn.classList.add('hidden');
        status.className = 'connection-status disconnected';
        status.innerHTML = '<span class="status-dot disconnected"></span><span>Desconectado</span>';
        input.disabled = true;
        sendBtn.disabled = true;
    }
}

function addSerialLine(text, type = 'received') {
    const output = document.getElementById('serialOutput');
    const line = document.createElement('div');
    line.className = `line ${type}`;
    line.textContent = text;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
}

function clearSerialOutput() {
    document.getElementById('serialOutput').innerHTML = '<div class="line system">Limpiado</div>';
}

// ============================================
// GESTIÓN DE PROYECTOS
// ============================================

function newProject() {
    if (confirm('¿Crear nuevo proyecto?')) {
        workspace.clear();
        addInitialBlocks();
        showToast('Nuevo proyecto', 'info');
    }
}

function saveProject() {
    const xml = Blockly.Xml.workspaceToDom(workspace);
    const xmlText = Blockly.Xml.domToText(xml);
    
    const blob = new Blob([xmlText], { type: 'application/xml' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'proyecto_arduino.maxide';
    a.click();
    
    showToast('Proyecto guardado', 'success');
}

function loadProject(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const xml = Blockly.utils.xml.textToDom(e.target.result);
            workspace.clear();
            Blockly.Xml.domToWorkspace(xml, workspace);
            showToast('Proyecto cargado', 'success');
        } catch (error) {
            showToast('Error al cargar', 'error');
        }
    };
    reader.readAsText(file);
    event.target.value = '';
}

// ============================================
// UTILIDADES
// ============================================

function copyCode() {
    navigator.clipboard.writeText(document.getElementById('codeOutput').textContent)
        .then(() => showToast('Código copiado', 'success'))
        .catch(() => showToast('Error al copiar', 'error'));
}

function updateBlockCount() {
    document.getElementById('blockCount').textContent = 
        `${workspace.getAllBlocks(false).length} bloques`;
}

function logToConsole(message, type = 'info') {
    const consoleEl = document.getElementById('consoleOutput');
    const time = new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    
    const line = document.createElement('div');
    line.className = `console-line ${type}`;
    line.innerHTML = `<span class="console-time">[${time}]</span><span>${escapeHtml(message)}</span>`;
    
    consoleEl.appendChild(line);
    consoleEl.scrollTop = consoleEl.scrollHeight;
}

function clearConsole() {
    document.getElementById('consoleOutput').innerHTML = '';
    logToConsole('Consola limpiada', 'info');
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <span class="toast-message">${escapeHtml(message)}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
