/**
 * MAX-IDE - Aplicación principal
 * Arduino Block Editor con Blockly
 * 
 * Arquitectura:
 * - Verificar: Servidor remoto (/api/compile/) - NO requiere Agent
 * - Subir: Agent local (localhost) con arduino-cli - REQUIERE Agent
 * - Serial Monitor: Web Serial API (opcional)
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

// Web Serial API (solo para Serial Monitor)
let serialPort = null;
let serialReader = null;
let serialWriter = null;
let readBuffer = '';

// Proyectos
let currentProjectId = null;

// ============================================
// AGENT LOCAL - Configuración y estado
// ============================================

const AgentConfig = {
    // URL base del Agent local (puerto 8765 por defecto)
    // Usamos 'localhost' en vez de '127.0.0.1' porque los navegadores
    // lo tratan como origen seguro y permiten peticiones desde HTTPS
    baseUrl: 'http://localhost:8765',
    
    // Estado del Agent
    available: false,
    lastCheck: null,
    lastError: null,
    version: null,
    platform: null,
    arduinoCli: null,
    
    // Control de reintentos (evitar spam)
    checkInterval: 15000,  // 15 segundos entre reintentos automáticos
    lastAutoCheck: 0,
    isChecking: false,
    
    // Timeout para requests al Agent
    timeout: 60000,  // 60s para uploads
    healthTimeout: 5000,  // 5s para health check
    
    // Endpoints del Agent
    endpoints: {
        health: '/health',
        upload: '/upload',
        ports: '/ports'
    }
};

// Diagnóstico del sistema
const DiagnosticInfo = {
    origin: '',
    isSecureContext: false,
    agentUrl: '',
    lastHealthStatus: null,
    lastError: null,
    browserInfo: '',
    timestamp: null
};

/**
 * Actualiza la información de diagnóstico
 */
function updateDiagnostics(healthResult = null) {
    DiagnosticInfo.origin = window.location.origin;
    DiagnosticInfo.isSecureContext = window.isSecureContext;
    DiagnosticInfo.agentUrl = AgentConfig.baseUrl;
    DiagnosticInfo.browserInfo = navigator.userAgent.split(' ').slice(-2).join(' ');
    DiagnosticInfo.timestamp = new Date().toISOString();
    
    if (healthResult !== null) {
        DiagnosticInfo.lastHealthStatus = healthResult.available ? 'connected' : 'disconnected';
        DiagnosticInfo.lastError = healthResult.error || null;
    }
}

/**
 * Verifica si el Agent local está disponible
 * NO hace spam de logs - solo loguea en cambios de estado o verificación manual
 * 
 * @param {boolean} manual - Si es una verificación manual (muestra logs siempre)
 * @returns {Promise<{available: boolean, version?: string, error?: string}>}
 */
async function checkAgentLocal(manual = false) {
    const url = AgentConfig.baseUrl + AgentConfig.endpoints.health;
    const now = Date.now();
    
    // Evitar múltiples checks simultáneos
    if (AgentConfig.isChecking) {
        return { available: AgentConfig.available, version: AgentConfig.version };
    }
    
    // Control de rate limiting para checks automáticos
    if (!manual && (now - AgentConfig.lastAutoCheck) < AgentConfig.checkInterval) {
        return { available: AgentConfig.available, version: AgentConfig.version };
    }
    
    AgentConfig.isChecking = true;
    AgentConfig.lastAutoCheck = now;
    
    // Solo loguear si es manual
    if (manual) {
        logToConsole('[AGENT] Verificando conexión con Agent local...', 'info');
    }
    
    const previousState = AgentConfig.available;
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), AgentConfig.healthTimeout);
        
        const response = await fetch(url, {
            method: 'GET',
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            const data = await response.json();
            
            AgentConfig.available = true;
            AgentConfig.lastCheck = now;
            AgentConfig.lastError = null;
            AgentConfig.version = data.version || 'unknown';
            AgentConfig.platform = data.platform || 'unknown';
            AgentConfig.arduinoCli = data.arduino_cli || null;
            
            // Solo loguear si cambió el estado o es manual
            if (!previousState || manual) {
                logToConsole(`[AGENT] ✓ Agent conectado v${AgentConfig.version}`, 'success');
                if (data.arduino_cli) {
                    logToConsole(`[AGENT] arduino-cli: ${data.arduino_cli_version || 'detectado'}`, 'info');
                }
            }
            
            // Guardar que el Agent fue instalado/conectado exitosamente
            try {
                localStorage.setItem('maxide_agent_installed', 'true');
                localStorage.setItem('maxide_agent_last_connected', new Date().toISOString());
            } catch (e) {}
            
            updateAgentUI(true);
            updateDiagnostics({ available: true });
            
            AgentConfig.isChecking = false;
            return { 
                available: true, 
                version: AgentConfig.version,
                platform: AgentConfig.platform
            };
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        let errorMsg = error.name === 'AbortError' ? 'Timeout' : error.message;
        let hint = '';
        
        // Detectar problemas comunes
        if (error.message === 'Failed to fetch' || error.message.includes('NetworkError')) {
            errorMsg = 'No se pudo conectar con el Agent';
            hint = '¿El Agent está corriendo? Ejecuta start_agent.sh (Linux/Mac) o start_agent.bat (Windows)';
        }
        
        AgentConfig.available = false;
        AgentConfig.lastCheck = now;
        AgentConfig.lastError = errorMsg;
        
        // Solo loguear si cambió el estado o es manual
        if (previousState || manual) {
            logToConsole(`[AGENT] ✗ Agent no disponible: ${errorMsg}`, 'warning');
            if (hint && manual) {
                logToConsole(`[AGENT] 💡 ${hint}`, 'info');
            }
        }
        
        updateAgentUI(false);
        updateDiagnostics({ available: false, error: errorMsg });
        
        AgentConfig.isChecking = false;
        return { available: false, error: errorMsg, hint };
    }
}

// Alias para compatibilidad
const checkAgentHealth = checkAgentLocal;

/**
 * Obtiene la lista de puertos del Agent local
 * @returns {Promise<Array>}
 */
async function getAgentPorts() {
    if (!AgentConfig.available) {
        return [];
    }
    
    const url = AgentConfig.baseUrl + AgentConfig.endpoints.ports;
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(url, {
            method: 'GET',
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            const data = await response.json();
            return data.ports || [];
        }
    } catch (error) {
        console.warn('[AGENT] Error obteniendo puertos:', error.message);
    }
    
    return [];
}

/**
 * Sube código al Arduino via Agent local
 * El Agent compila y sube el código localmente usando arduino-cli
 * 
 * @param {string} code - Código Arduino
 * @param {string} port - Puerto serial (ej: /dev/ttyUSB0, COM3)
 * @param {string} fqbn - Board FQBN (ej: arduino:avr:uno)
 * @param {Function} onLog - Callback para logs
 * @returns {Promise<{success: boolean, message?: string, error?: string, logs?: Array}>}
 */
async function uploadViaAgent(code, port, fqbn, onLog = () => {}) {
    onLog('[UPLOAD-AGENT] Iniciando proceso de upload...');
    onLog(`[UPLOAD-AGENT] Puerto: ${port}, Placa: ${fqbn}`);
    
    // ========================================
    // Enviar código directamente al Agent
    // El Agent compila y sube localmente
    // ========================================
    const agentUrl = AgentConfig.baseUrl + AgentConfig.endpoints.upload;
    onLog('[UPLOAD-AGENT] Enviando código al Agent local...');
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 180000); // 3 min timeout para compilar+upload
        
        const response = await fetch(agentUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                port: port,
                fqbn: fqbn,
                code: code  // Enviar código directamente, el Agent compila localmente
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        const data = await response.json();
        
        // Log de respuesta del Agent
        if (data.logs && Array.isArray(data.logs)) {
            data.logs.forEach(log => onLog(`[AGENT] ${log}`));
        }
        
        if (response.ok && (data.ok || data.success)) {
            onLog('[UPLOAD-AGENT] ✓ Upload completado exitosamente');
            return {
                success: true,
                message: data.message || 'Código subido exitosamente',
                logs: data.logs
            };
        } else {
            const errorMsg = data.error || `HTTP ${response.status}`;
            onLog(`[UPLOAD-AGENT] ✗ Error: ${errorMsg}`);
            
            // Mostrar hint si existe
            if (data.hint) {
                onLog(`[UPLOAD-AGENT] 💡 Sugerencia: ${data.hint}`);
            }
            
            return {
                success: false,
                error: errorMsg,
                errorCode: data.error_code,
                hint: data.hint,
                logs: data.logs
            };
        }
    } catch (error) {
        const errorMsg = error.name === 'AbortError' 
            ? 'Timeout - El Agent no respondió a tiempo (¿compilación muy larga?)'
            : error.message;
        onLog(`[UPLOAD-AGENT] ✗ Error de conexión: ${errorMsg}`);
        return {
            success: false,
            error: errorMsg
        };
    }
}

/**
 * Detecta el sistema operativo del usuario
 */
function detectUserOS() {
    const userAgent = navigator.userAgent.toLowerCase();
    if (userAgent.includes('win')) return 'windows';
    if (userAgent.includes('mac')) return 'mac';
    return 'linux';
}

/**
 * Verifica si el Agent fue instalado previamente
 */
function wasAgentInstalled() {
    try {
        return localStorage.getItem('maxide_agent_installed') === 'true';
    } catch (e) {
        return false;
    }
}

/**
 * Obtiene el comando para iniciar el Agent según el OS
 */
function getStartCommand() {
    const os = detectUserOS();
    if (os === 'windows') {
        return 'start_agent.bat';
    } else {
        return 'bash start_agent.sh';
    }
}

/**
 * Actualiza la UI según el estado del Agent
 */
function updateAgentUI(available) {
    const btnUpload = document.getElementById('btnUpload');
    const agentBanner = document.getElementById('agentBanner');
    const agentStatusDot = document.getElementById('agentStatusDot');
    const agentStatusText = document.getElementById('agentStatusText');
    const agentStatusContainer = document.getElementById('agentStatus');
    
    if (btnUpload) {
        if (available) {
            btnUpload.disabled = false;
            btnUpload.title = 'Subir código al Arduino';
            btnUpload.classList.remove('btn-disabled');
        } else {
            btnUpload.disabled = true;
            btnUpload.title = 'Requiere Agent local - Haz clic en "Cómo instalar"';
            btnUpload.classList.add('btn-disabled');
        }
    }
    
    // Mostrar/ocultar banner de Agent y actualizar contenido
    if (agentBanner) {
        if (available) {
            agentBanner.style.display = 'none';
        } else {
            agentBanner.style.display = 'flex';
            
            // Verificar si el Agent ya fue instalado antes
            const alreadyInstalled = wasAgentInstalled();
            const bannerTextEl = agentBanner.querySelector('.agent-banner-text');
            const installBtn = document.getElementById('btnInstallAgent');
            
            if (alreadyInstalled && bannerTextEl) {
                // Ya instalado - mostrar mensaje simple para ejecutar
                const startCmd = getStartCommand();
                const os = detectUserOS();
                const osEmoji = os === 'windows' ? '🪟' : (os === 'mac' ? '🍎' : '🐧');
                
                bannerTextEl.innerHTML = `
                    <strong>Agent no está corriendo</strong>
                    <span>${osEmoji} Ejecuta <code style="background:#1e2530;padding:2px 6px;border-radius:4px;">${startCmd}</code> en la carpeta del Agent</span>
                `;
                
                if (installBtn) {
                    installBtn.innerHTML = '📂 Ver ubicación';
                }
            } else if (bannerTextEl) {
                // Primera vez - mostrar mensaje de instalación
                bannerTextEl.innerHTML = `
                    <strong>Agent local requerido para subir código</strong>
                    <span>Instala el MAX-IDE Agent en tu PC para poder subir código al Arduino</span>
                `;
                
                if (installBtn) {
                    installBtn.innerHTML = '📥 Instrucciones de instalación';
                }
            }
        }
    }
    
    // Actualizar indicador en status bar
    if (agentStatusDot) {
        if (available) {
            agentStatusDot.classList.remove('disconnected');
            agentStatusDot.classList.add('connected');
        } else {
            agentStatusDot.classList.add('disconnected');
            agentStatusDot.classList.remove('connected');
        }
    }
    
    if (agentStatusText) {
        if (available) {
            agentStatusText.textContent = `Agent: v${AgentConfig.version || '?'}`;
            agentStatusText.title = `Plataforma: ${AgentConfig.platform || 'N/A'}\narduino-cli: ${AgentConfig.arduinoCli || 'N/A'}`;
        } else {
            agentStatusText.textContent = 'Agent: Desconectado';
            agentStatusText.title = `Último error: ${AgentConfig.lastError || 'N/A'}\nURL: ${AgentConfig.baseUrl}`;
        }
    }
    
    // Hacer clickeable el status para diagnóstico
    if (agentStatusContainer && !agentStatusContainer._hasClickHandler) {
        agentStatusContainer.style.cursor = 'pointer';
        agentStatusContainer.addEventListener('click', showDiagnosticPanel);
        agentStatusContainer._hasClickHandler = true;
    }
}

/**
 * Muestra ayuda para encontrar la ubicación del Agent instalado
 */
function showAgentLocationHelp() {
    const os = detectUserOS();
    const startCmd = getStartCommand();
    
    let helpText = '';
    
    if (os === 'windows') {
        helpText = `🔍 UBICACIÓN DEL AGENT

El Agent está en la carpeta donde lo extrajiste del ZIP.

📁 LUGARES COMUNES:
• Descargas (Downloads)\\maxide-agent
• Escritorio (Desktop)\\maxide-agent
• Documentos\\maxide-agent

📝 PASOS:
1. Abre el Explorador de archivos (presiona Windows + E)
2. Busca una carpeta llamada "maxide-agent"
3. Dentro de esa carpeta, haz doble clic en: ${startCmd}

💡 TIP: Si no la encuentras, busca "start_agent.bat" en el buscador de Windows (Windows + S).`;
    } else if (os === 'mac') {
        helpText = `🔍 UBICACIÓN DEL AGENT

El Agent está en la carpeta donde lo extrajiste del ZIP.

📁 LUGARES COMUNES:
• ~/Downloads/maxide-agent
• ~/Desktop/maxide-agent
• ~/Documents/maxide-agent

📝 PASOS:
1. Abre Finder
2. Busca una carpeta llamada "maxide-agent"
3. Abre Terminal en esa carpeta (clic derecho → "Nueva Terminal en la carpeta")
4. Ejecuta: ${startCmd}

💡 TIP: Puedes arrastrar la carpeta a Terminal para obtener la ruta.`;
    } else {
        // Linux
        helpText = `🔍 UBICACIÓN DEL AGENT

El Agent está en la carpeta donde lo extrajiste del ZIP.

📁 LUGARES COMUNES:
• ~/Downloads/maxide-agent
• ~/Desktop/maxide-agent
• ~/Documents/maxide-agent

📝 PASOS:
1. Abre el administrador de archivos
2. Busca una carpeta llamada "maxide-agent"
3. Abre Terminal en esa carpeta
4. Ejecuta: ${startCmd}

💡 TIP: Puedes usar: find ~ -name "maxide-agent" -type d`;
    }
    
    // Preguntar si quiere ver las instrucciones de instalación
    const userChoice = confirm(helpText + '\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n¿No lo encuentras o lo eliminaste?\n\nPresiona ACEPTAR para ver las instrucciones de instalación completas.\nPresiona CANCELAR para cerrar este mensaje.');
    
    if (userChoice) {
        // Resetear el estado de instalación y mostrar instrucciones
        resetAgentInstallStatus();
        showAgentInstallModal();
    }
}

/**
 * Resetea el estado de instalación del Agent en localStorage
 */
function resetAgentInstallStatus() {
    try {
        localStorage.removeItem('maxide_agent_installed');
        localStorage.removeItem('maxide_agent_last_connected');
    } catch (e) {}
    
    // Actualizar la UI
    updateAgentUI(false);
}

/**
 * Muestra el panel de diagnóstico
 */
function showDiagnosticPanel() {
    updateDiagnostics();
    
    const info = `
╔═══════════════════════════════════════════════════╗
║           DIAGNÓSTICO MAX-IDE AGENT               ║
╠═══════════════════════════════════════════════════╣
║ Origin:          ${DiagnosticInfo.origin}
║ Secure Context:  ${DiagnosticInfo.isSecureContext ? 'Sí (HTTPS)' : 'No (HTTP)'}
║ Agent URL:       ${DiagnosticInfo.agentUrl}
║ Estado:          ${DiagnosticInfo.lastHealthStatus || 'No verificado'}
║ Último error:    ${DiagnosticInfo.lastError || 'Ninguno'}
║ Versión Agent:   ${AgentConfig.version || 'N/A'}
║ Plataforma:      ${AgentConfig.platform || 'N/A'}
║ arduino-cli:     ${AgentConfig.arduinoCli || 'No detectado'}
║ Timestamp:       ${DiagnosticInfo.timestamp}
╚═══════════════════════════════════════════════════╝

${!AgentConfig.available ? `
⚠️ SOLUCIÓN:
1. Descarga el Agent desde el botón "Cómo instalar"
2. Descomprime y ejecuta start_agent (Windows: .bat, Linux/Mac: .sh)
3. El Agent debe estar corriendo en ${AgentConfig.baseUrl}
4. Haz clic en "Verificar conexión" para reintentar
` : '✓ Agent funcionando correctamente'}
    `.trim();
    
    // Loguear en consola del IDE
    logToConsole('=== DIAGNÓSTICO ===', 'info');
    logToConsole(`Origin: ${DiagnosticInfo.origin}`, 'info');
    logToConsole(`Secure: ${DiagnosticInfo.isSecureContext}`, 'info');
    logToConsole(`Agent URL: ${DiagnosticInfo.agentUrl}`, 'info');
    logToConsole(`Estado: ${DiagnosticInfo.lastHealthStatus || 'No verificado'}`, 
                 DiagnosticInfo.lastHealthStatus === 'connected' ? 'success' : 'warning');
    if (DiagnosticInfo.lastError) {
        logToConsole(`Error: ${DiagnosticInfo.lastError}`, 'error');
    }
    
    // También mostrar en consola del navegador
    console.log(info);
    
    // Mostrar toast con resumen
    if (AgentConfig.available) {
        showToast(`Agent v${AgentConfig.version} conectado`, 'success');
    } else {
        showToast(`Agent desconectado - ${AgentConfig.lastError || 'No disponible'}`, 'warning');
    }
}

/**
 * Muestra el modal de instalación del Agent
 */
function showAgentInstallModal() {
    const modal = document.getElementById('agentInstallModal');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('active');
    }
}

/**
 * Cierra el modal de instalación del Agent
 */
function closeAgentInstallModal() {
    const modal = document.getElementById('agentInstallModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
}

/**
 * Cambia la pestaña de instrucciones del Agent (Windows/Mac/Linux)
 */
function switchAgentTab(os) {
    // Actualizar tabs
    document.querySelectorAll('.agent-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.getAttribute('data-os') === os) {
            tab.classList.add('active');
        }
    });
    
    // Mostrar instrucciones correspondientes
    document.querySelectorAll('.agent-instructions').forEach(instr => {
        instr.style.display = 'none';
    });
    
    const targetInstr = document.getElementById(`instructions-${os}`);
    if (targetInstr) {
        targetInstr.style.display = 'block';
    }
}

/**
 * Verifica la conexión del Agent desde el modal
 */
async function verifyAgentFromModal() {
    const statusEl = document.getElementById('agentVerifyStatus');
    if (statusEl) {
        statusEl.className = 'agent-verify-status checking';
        statusEl.textContent = 'Verificando...';
    }
    
    // Verificación manual - siempre muestra logs
    const result = await checkAgentLocal(true);
    
    if (statusEl) {
        if (result.available) {
            statusEl.className = 'agent-verify-status success';
            statusEl.textContent = `✓ Conectado v${result.version}`;
            setTimeout(() => {
                closeAgentInstallModal();
                showToast('¡Agent conectado correctamente!', 'success');
                // Refrescar puertos después de conectar
                refreshPorts();
            }, 1500);
        } else {
            statusEl.className = 'agent-verify-status error';
            statusEl.textContent = `✗ ${result.error || 'No disponible'}`;
        }
    }
}

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
        'servo_category': { 'colour': '#a855f7' },
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
    
    // Inicializar diagnósticos
    updateDiagnostics();
    
    // Log inicial (una sola vez)
    logToConsole('MAX-IDE v2.0 inicializado', 'info');
    logToConsole(`Agent URL: ${AgentConfig.baseUrl}`, 'info');
    
    // Verificar Agent local (verificación manual = muestra logs)
    checkAgentLocal(true).then(result => {
        if (!result.available) {
            // El banner ya se muestra via updateAgentUI
            logToConsole('💡 Instala el Agent local para subir código al Arduino', 'warning');
        }
        // Cargar puertos después de verificar Agent
        refreshPorts();
    });
    
    // Monitoreo periódico del Agent (silencioso, no spamea logs)
    // Solo reintenta cada 15 segundos y solo loguea si hay cambio de estado
    setInterval(() => {
        checkAgentLocal(false);  // false = automático, no loguea si no hay cambio
    }, AgentConfig.checkInterval);
});

/**
 * Muestra el banner de Agent no disponible
 */
function showAgentBanner() {
    // Verificar si ya existe el banner
    if (document.getElementById('agentBanner')) return;
    
    const banner = document.createElement('div');
    banner.id = 'agentBanner';
    banner.className = 'agent-banner';
    banner.innerHTML = `
        <div class="agent-banner-content">
            <span class="agent-banner-icon">⚠️</span>
            <span class="agent-banner-text">
                <strong>Agent local no detectado.</strong>
                Para subir código, instala y ejecuta el MAX-IDE Agent en tu PC.
            </span>
            <button class="btn btn-sm btn-primary" onclick="checkAgentHealth()">
                🔄 Verificar conexión
            </button>
            <button class="btn btn-sm btn-ghost" onclick="this.parentElement.parentElement.style.display='none'">
                ✕
            </button>
        </div>
    `;
    
    // Insertar al inicio del body o después del header
    const header = document.querySelector('.header');
    if (header && header.nextSibling) {
        header.parentNode.insertBefore(banner, header.nextSibling);
    } else {
        document.body.insertBefore(banner, document.body.firstChild);
    }
    
    // Agregar estilos si no existen
    if (!document.getElementById('agentBannerStyles')) {
        const style = document.createElement('style');
        style.id = 'agentBannerStyles';
        style.textContent = `
            .agent-banner {
                background: linear-gradient(135deg, #f59e0b22, #ef444422);
                border-bottom: 1px solid #f59e0b44;
                padding: 10px 20px;
                display: flex;
                justify-content: center;
            }
            .agent-banner-content {
                display: flex;
                align-items: center;
                gap: 12px;
                max-width: 1200px;
            }
            .agent-banner-icon {
                font-size: 20px;
            }
            .agent-banner-text {
                color: #e6edf3;
                font-size: 13px;
            }
            .agent-banner-text strong {
                color: #f59e0b;
            }
        `;
        document.head.appendChild(style);
    }
}

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
    document.getElementById('btnCompile').addEventListener('click', verifyCode);
    document.getElementById('btnUpload').addEventListener('click', uploadCode);
    document.getElementById('btnRefreshPorts').addEventListener('click', refreshPorts);
    document.getElementById('btnAddPort').addEventListener('click', refreshPorts); // Refresca desde Agent
    
    // Botones de archivo
    document.getElementById('btnNew').addEventListener('click', newProject);
    document.getElementById('btnSave').addEventListener('click', saveProject);
    document.getElementById('btnLoad').addEventListener('click', () => document.getElementById('fileInput').click());
    document.getElementById('fileInput').addEventListener('change', loadProject);
    
    // Botones de proyectos (si existen)
    const btnSaveProject = document.getElementById('btnSaveProject');
    const btnLoadProject = document.getElementById('btnLoadProject');
    if (btnSaveProject) {
        btnSaveProject.addEventListener('click', saveProjectToServer);
    }
    if (btnLoadProject) {
        btnLoadProject.addEventListener('click', openProjectsModal);
    }
    
    // Modal de proyectos
    const projectsModal = document.getElementById('projectsModal');
    const createProjectModal = document.getElementById('createProjectModal');
    if (projectsModal) {
        document.getElementById('btnCloseProjects')?.addEventListener('click', () => {
            projectsModal.style.display = 'none';
        });
        document.getElementById('btnCreateNewProject')?.addEventListener('click', () => {
            projectsModal.style.display = 'none';
            if (createProjectModal) createProjectModal.style.display = 'flex';
        });
        document.getElementById('btnCancelCreateProject')?.addEventListener('click', () => {
            if (createProjectModal) createProjectModal.style.display = 'none';
        });
        document.getElementById('btnConfirmCreateProject')?.addEventListener('click', createNewProject);
        document.getElementById('btnCloseCreateProject')?.addEventListener('click', () => {
            if (createProjectModal) createProjectModal.style.display = 'none';
        });
    }
    
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
                case 'r': e.preventDefault(); verifyCode(); break;
            }
        }
    });
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
// GESTIÓN DE PUERTOS (Agent local)
// ============================================

/**
 * Refresca la lista de puertos desde el Agent local
 */
async function refreshPorts() {
    const select = document.getElementById('portSelect');
    const serialSelect = document.getElementById('serialPortSelect');
    const btn = document.getElementById('btnRefreshPorts');
    
    btn.innerHTML = '<span class="loading"></span>';
    
    try {
        // Primero verificar si el Agent está disponible
        if (!AgentConfig.available) {
            await checkAgentHealth();
        }
        
        if (AgentConfig.available) {
            // Obtener puertos del Agent local
            const ports = await getAgentPorts();
            
            if (ports.length > 0) {
                const optionsHtml = '<option value="">Seleccionar puerto...</option>' +
                    ports.map(port => {
                        const device = port.device || port.address || port;
                        const desc = port.description || port.board_name || '';
                        const label = desc ? `${device} - ${desc}` : device;
                        return `<option value="${device}">${label}</option>`;
                    }).join('');
                
                select.innerHTML = optionsHtml;
                if (serialSelect) serialSelect.innerHTML = optionsHtml;
                
                logToConsole(`[AGENT] ${ports.length} puerto(s) disponible(s)`, 'success');
                
                // Auto-seleccionar si solo hay uno
                if (ports.length === 1) {
                    const device = ports[0].device || ports[0].address || ports[0];
                    select.value = device;
                    if (serialSelect) serialSelect.value = device;
                    currentPort = device;
                    updateConnectionStatus();
                }
            } else {
                select.innerHTML = '<option value="">No hay puertos disponibles</option>';
                if (serialSelect) serialSelect.innerHTML = '<option value="">No hay puertos disponibles</option>';
                logToConsole('[AGENT] No se encontraron puertos seriales', 'warning');
            }
        } else {
            // Agent no disponible - mostrar mensaje
            select.innerHTML = '<option value="">⚠️ Agent no disponible</option>';
            if (serialSelect) serialSelect.innerHTML = '<option value="">⚠️ Agent no disponible</option>';
            logToConsole('[AGENT] Agent local no disponible. Instala el Agent para ver puertos.', 'warning');
        }
    } catch (error) {
        logToConsole('[AGENT] Error al buscar puertos: ' + error.message, 'error');
        select.innerHTML = '<option value="">Error obteniendo puertos</option>';
    }
    
    btn.innerHTML = '🔄';
}

function updateConnectionStatus() {
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('statusText');
    
    if (isSerialConnected) {
        dot.classList.remove('disconnected');
        text.textContent = 'Serial: Conectado';
    } else if (currentPort) {
        dot.classList.remove('disconnected');
        text.textContent = `Puerto: ${currentPort}`;
    } else if (AgentConfig.available) {
        dot.classList.add('disconnected');
        text.textContent = 'Agent OK - Sin puerto';
    } else {
        dot.classList.add('disconnected');
        text.textContent = 'Agent no disponible';
    }
}

// ============================================
// VERIFICAR CÓDIGO (Servidor - sin Agent)
// ============================================

/**
 * Verifica/compila el código en el servidor
 * NO requiere Agent local
 */
async function verifyCode() {
    const btn = document.getElementById('btnCompile');
    const code = arduinoGenerator.workspaceToCode(workspace);
    
    if (!code.trim()) {
        showToast('No hay código para verificar', 'warning');
        return;
    }
    
    // Verificar que el Agent esté disponible
    if (!AgentConfig.available) {
        logToConsole('[VERIFY] ✗ Agent no disponible. Instálalo para verificar código.', 'error');
        showToast('Instala el Agent para verificar código', 'warning');
        showAgentInstallModal();
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> Verificando...';
    logToConsole('[VERIFY] Compilando código en tu PC...', 'info');
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 min timeout
        
        const response = await fetch(AgentConfig.baseUrl + '/compile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, fqbn: currentBoard }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        const data = await response.json();
        
        // Mostrar logs de compilación
        if (data.logs && Array.isArray(data.logs)) {
            data.logs.slice(-10).forEach(log => logToConsole(`[COMPILE] ${log}`, 'info'));
        }
        
        if (data.ok) {
            logToConsole(`[VERIFY] ✓ Verificación exitosa (${data.size || '?'} bytes)`, 'success');
            showToast(`Verificación exitosa (${data.size || '?'} bytes)`, 'success');
        } else {
            logToConsole('[VERIFY] ✗ Error de verificación', 'error');
            
            // Mostrar errores detallados
            if (data.error) {
                const errorLines = data.error.split('\n').filter(l => l.trim()).slice(-5);
                errorLines.forEach(line => logToConsole(`[ERROR] ${line}`, 'error'));
            }
            
            showToast('Error de verificación', 'error');
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            logToConsole('[VERIFY] ✗ Timeout: la compilación tardó más de 2 minutos', 'error');
            showToast('Timeout de compilación', 'error');
        } else {
            logToConsole(`[VERIFY] ✗ Error de conexión: ${error.message}`, 'error');
            logToConsole('[VERIFY] ¿El Agent está corriendo?', 'warning');
            showToast('Error conectando con Agent', 'error');
        }
    }
    
    btn.disabled = false;
    btn.innerHTML = '<span>⚙️</span><span>Verificar</span>';
}

// ============================================
// SUBIR CÓDIGO (Agent local - arduino-cli)
// ============================================

/**
 * Sube el código al Arduino via Agent local
 * REQUIERE Agent local ejecutándose
 */
async function uploadCode() {
    const btn = document.getElementById('btnUpload');
    const code = arduinoGenerator.workspaceToCode(workspace);
    
    // Validar código
    if (!code.trim()) {
        showToast('No hay código para subir', 'warning');
        return;
    }
    
    // Validar puerto seleccionado
    if (!currentPort) {
        showToast('Selecciona un puerto primero', 'warning');
        logToConsole('[UPLOAD-AGENT] No hay puerto seleccionado', 'warning');
        return;
    }
    
    // Verificar disponibilidad del Agent
    if (!AgentConfig.available) {
        logToConsole('[UPLOAD-AGENT] Agent no disponible, verificando...', 'info');
        const healthCheck = await checkAgentHealth();
        
        if (!healthCheck.available) {
            showToast('Agent local no disponible. Instala y ejecuta el MAX-IDE Agent.', 'error');
            logToConsole('[UPLOAD-AGENT] ✗ No se puede subir sin Agent local', 'error');
            showAgentBanner();
            return;
        }
    }
    
    // Desconectar Serial Monitor si está conectado (para liberar el puerto)
    if (isSerialConnected) {
        logToConsole('[UPLOAD-AGENT] Desconectando Serial Monitor...', 'info');
        await disconnectSerial();
        await new Promise(r => setTimeout(r, 500));
    }
    
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> Subiendo...';
    logToConsole('[UPLOAD-AGENT] Iniciando upload via Agent local...', 'info');
    logToConsole(`[UPLOAD-AGENT] Puerto: ${currentPort}, Placa: ${currentBoard}`, 'info');
    
    try {
        const result = await uploadViaAgent(code, currentPort, currentBoard, (msg) => {
            logToConsole(msg, 'info');
        });
        
        if (result.success) {
            logToConsole('[UPLOAD-AGENT] ✓ ¡Código subido exitosamente!', 'success');
            showToast('¡Código subido exitosamente!', 'success');
        } else {
            logToConsole(`[UPLOAD-AGENT] ✗ Error: ${result.error}`, 'error');
            
            // Sugerencias según el tipo de error
            if (result.errorCode === 'PORT_BUSY' || result.error.includes('busy')) {
                showToast('Puerto ocupado. Cierra otras aplicaciones que lo usen.', 'error');
            } else if (result.errorCode === 'PORT_NOT_FOUND' || result.error.includes('not found')) {
                showToast('Puerto no encontrado. Verifica la conexión del Arduino.', 'error');
            } else if (result.errorCode === 'UPLOAD_SYNC_FAIL' || result.error.includes('sync')) {
                showToast('Error de sincronización. Presiona RESET en el Arduino y reintenta.', 'error');
            } else {
                showToast(`Error: ${result.error}`, 'error');
            }
        }
    } catch (error) {
        logToConsole(`[UPLOAD-AGENT] ✗ Error inesperado: ${error.message}`, 'error');
        showToast('Error de conexión con Agent', 'error');
    }
    
    btn.disabled = false;
    btn.innerHTML = '<span>🚀</span><span>Subir</span>';
}

// ============================================
// MONITOR SERIAL (Web Serial API)
// ============================================

function openSerialMonitor() {
    document.getElementById('serialModal').classList.add('active');
    
    // Verificar soporte de Web Serial API
    if (!('serial' in navigator)) {
        addSerialLine('⚠️ Web Serial API no está disponible en este navegador.', 'system');
        addSerialLine('Usa Chrome, Edge u Opera con HTTPS para el Monitor Serial.', 'system');
        logToConsole('Web Serial API no disponible', 'warning');
        document.getElementById('btnSerialConnect').disabled = true;
    } else {
        document.getElementById('btnSerialConnect').disabled = false;
        addSerialLine('ℹ️ Haz clic en "Conectar" para seleccionar un puerto serial.', 'system');
    }
}

function closeSerialMonitor() {
    document.getElementById('serialModal').classList.remove('active');
}

async function connectSerial() {
    const baudrate = parseInt(document.getElementById('serialBaudrate').value);
    
    if (!('serial' in navigator)) {
        showToast('Web Serial API no disponible', 'error');
        return;
    }
    
    try {
        // Solicitar puerto al usuario
        serialPort = await navigator.serial.requestPort();
        addSerialLine(`Puerto seleccionado`, 'system');
        
        // Si el puerto ya está abierto, cerrarlo primero
        if (serialPort.readable || serialPort.writable) {
            try {
                await serialPort.close();
            } catch (e) {}
        }
        
        // Abrir conexión
        await serialPort.open({ baudRate: baudrate });
        
        // Configurar lectura
        const decoder = new TextDecoderStream();
        const inputStream = serialPort.readable.pipeThrough(decoder);
        serialReader = inputStream.getReader();
        
        // Configurar escritura
        const encoder = new TextEncoderStream();
        const outputStream = serialPort.writable.pipeThrough(encoder);
        serialWriter = outputStream.getWriter();
        
        isSerialConnected = true;
        updateSerialUI(true, 'Serial', baudrate);
        addSerialLine(`Conectado @ ${baudrate} baud`, 'system');
        updateConnectionStatus();
        
        // Iniciar lectura continua
        readSerialData().catch(console.error);
        
        showToast('Monitor serial conectado', 'success');
        logToConsole('Monitor serial conectado (Web Serial)', 'success');
        
    } catch (error) {
        if (error.name === 'NotFoundError') {
            showToast('No se seleccionó ningún puerto', 'warning');
        } else {
            showToast('Error al conectar: ' + error.message, 'error');
        }
        logToConsole('Error serial: ' + error.message, 'error');
        serialPort = null;
    }
}

async function disconnectSerial() {
    try {
        if (serialReader) {
            await serialReader.cancel();
            serialReader.releaseLock();
            serialReader = null;
        }
        
        if (serialWriter) {
            await serialWriter.close();
            serialWriter = null;
        }
        
        if (serialPort) {
            await serialPort.close();
            serialPort = null;
        }
        
        isSerialConnected = false;
        updateSerialUI(false);
        updateConnectionStatus();
        addSerialLine('Desconectado', 'system');
        logToConsole('Monitor serial desconectado', 'info');
        
    } catch (error) {
        console.error('Error al desconectar:', error);
        isSerialConnected = false;
        updateSerialUI(false);
    }
}

async function readSerialData() {
    if (!isSerialConnected || !serialReader) return;
    
    try {
        while (isSerialConnected && serialReader) {
            const { value, done } = await serialReader.read();
            
            if (done) {
                serialReader.releaseLock();
                break;
            }
            
            if (value) {
                readBuffer += value;
                
                const lines = readBuffer.split('\n');
                readBuffer = lines.pop() || '';
                
                lines.forEach(line => {
                    if (line.trim()) {
                        addSerialLine(line.trim(), 'received');
                    }
                });
            }
        }
    } catch (error) {
        if (error.name !== 'NetworkError' && isSerialConnected) {
            await disconnectSerial();
            showToast('Error de lectura serial', 'error');
        }
    }
}

async function sendSerialData() {
    if (!isSerialConnected || !serialWriter) return;
    
    const input = document.getElementById('serialInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    try {
        await serialWriter.write(message + '\n');
        addSerialLine(`> ${message}`, 'sent');
        input.value = '';
    } catch (error) {
        showToast('Error al enviar: ' + error.message, 'error');
        if (isSerialConnected) {
            await disconnectSerial();
        }
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
    const time = new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    
    const line = document.createElement('div');
    line.className = `console-line ${type}`;
    line.innerHTML = `<span class="console-time">[${time}]</span><span>${escapeHtml(message)}</span>`;
    
    consoleEl.appendChild(line);
    consoleEl.scrollTop = consoleEl.scrollHeight;
    
    // También log a consola del navegador
    console.log(`[MAX-IDE] ${message}`);
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

// ============================================
// GESTIÓN DE PROYECTOS EN SERVIDOR
// ============================================

async function saveProjectToServer() {
    if (!workspace) {
        showToast('No hay workspace disponible', 'error');
        return;
    }
    
    const xml = Blockly.Xml.workspaceToDom(workspace);
    const xmlText = Blockly.Xml.domToText(xml);
    const code = arduinoGenerator.workspaceToCode(workspace);
    
    if (!currentProjectId) {
        const name = prompt('Nombre del proyecto:');
        if (!name) return;
        
        try {
            const response = await fetch('/api/projects/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ name, description: '' })
            });
            
            const data = await response.json();
            if (data.success) {
                currentProjectId = data.project_id;
            } else {
                showToast('Error al crear proyecto: ' + data.error, 'error');
                return;
            }
        } catch (error) {
            showToast('Error: ' + error.message, 'error');
            return;
        }
    }
    
    try {
        const response = await fetch('/api/projects/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                project_id: currentProjectId,
                name: document.getElementById('projectName')?.value || 'Proyecto sin nombre',
                xml_content: xmlText,
                arduino_code: code
            })
        });
        
        const data = await response.json();
        if (data.success) {
            showToast('Proyecto guardado exitosamente', 'success');
            logToConsole('Proyecto guardado en el servidor', 'success');
        } else {
            showToast('Error al guardar: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function openProjectsModal() {
    const modal = document.getElementById('projectsModal');
    if (!modal) return;
    
    modal.style.display = 'flex';
    await loadProjectsList();
}

async function loadProjectsList() {
    const listDiv = document.getElementById('projectsList');
    if (!listDiv) return;
    
    listDiv.innerHTML = '<div style="text-align: center; padding: 20px; color: #8b949e;">Cargando proyectos...</div>';
    
    try {
        const response = await fetch('/api/projects/list/');
        const data = await response.json();
        
        if (data.success) {
            if (data.projects.length === 0) {
                listDiv.innerHTML = '<div style="text-align: center; padding: 20px; color: #8b949e;">No tienes proyectos aún</div>';
            } else {
                listDiv.innerHTML = data.projects.map(project => `
                    <div style="padding: 15px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #58a6ff;">${escapeHtml(project.name)}</strong>
                            <div style="color: #8b949e; font-size: 12px; margin-top: 5px;">
                                ${new Date(project.updated_at).toLocaleString('es-ES')}
                            </div>
                        </div>
                        <button class="btn btn-sm btn-primary" onclick="loadProjectFromServer(${project.id})">Cargar</button>
                    </div>
                `).join('');
            }
        } else {
            listDiv.innerHTML = '<div style="text-align: center; padding: 20px; color: #f85149;">Error al cargar proyectos</div>';
        }
    } catch (error) {
        listDiv.innerHTML = '<div style="text-align: center; padding: 20px; color: #f85149;">Error: ' + error.message + '</div>';
    }
}

async function loadProjectFromServer(projectId) {
    try {
        const response = await fetch(`/api/projects/load/${projectId}/`);
        const data = await response.json();
        
        if (data.success && data.project) {
            currentProjectId = data.project.id;
            
            if (data.project.xml_content) {
                const xml = Blockly.utils.xml.textToDom(data.project.xml_content);
                workspace.clear();
                Blockly.Xml.domToWorkspace(xml, workspace);
                updateCode();
            }
            
            const modal = document.getElementById('projectsModal');
            if (modal) modal.style.display = 'none';
            
            showToast('Proyecto cargado exitosamente', 'success');
            logToConsole(`Proyecto "${data.project.name}" cargado`, 'success');
        } else {
            showToast('Error al cargar proyecto: ' + (data.error || 'Error desconocido'), 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function createNewProject() {
    const nameInput = document.getElementById('projectName');
    const descInput = document.getElementById('projectDescription');
    
    if (!nameInput || !nameInput.value.trim()) {
        showToast('El nombre del proyecto es requerido', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/projects/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                name: nameInput.value.trim(),
                description: descInput ? descInput.value.trim() : ''
            })
        });
        
        const data = await response.json();
        if (data.success) {
            currentProjectId = data.project_id;
            
            const createModal = document.getElementById('createProjectModal');
            if (createModal) createModal.style.display = 'none';
            
            nameInput.value = '';
            if (descInput) descInput.value = '';
            
            showToast('Proyecto creado exitosamente', 'success');
            logToConsole('Nuevo proyecto creado', 'success');
        } else {
            showToast('Error al crear proyecto: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

// Función para cargar proyecto desde template
window.loadProjectFromTemplate = function(xmlContent, projectId) {
    if (workspace && xmlContent) {
        try {
            const xml = Blockly.utils.xml.textToDom(xmlContent);
            workspace.clear();
            Blockly.Xml.domToWorkspace(xml, workspace);
            updateCode();
            if (projectId) currentProjectId = projectId;
        } catch (e) {
            console.error('Error cargando proyecto:', e);
        }
    }
};

// Exponer funciones globalmente para botones HTML
window.checkAgentHealth = checkAgentHealth;
window.checkAgentLocal = checkAgentLocal;
window.showAgentInstallModal = showAgentInstallModal;
window.closeAgentInstallModal = closeAgentInstallModal;
window.switchAgentTab = switchAgentTab;
window.verifyAgentFromModal = verifyAgentFromModal;
window.showDiagnosticPanel = showDiagnosticPanel;

// Inicializar event listeners para Agent UI cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Botones del banner del Agent
    const btnCheckAgent = document.getElementById('btnCheckAgent');
    const btnInstallAgent = document.getElementById('btnInstallAgent');
    
    if (btnCheckAgent) {
        btnCheckAgent.addEventListener('click', () => {
            // Verificación manual - siempre muestra logs
            checkAgentLocal(true);
        });
    }
    
    if (btnInstallAgent) {
        btnInstallAgent.addEventListener('click', function() {
            // Si el Agent ya fue instalado, mostrar ayuda para encontrar la carpeta
            if (wasAgentInstalled()) {
                showAgentLocationHelp();
            } else {
                // Primera vez - mostrar instrucciones de instalación
                showAgentInstallModal();
            }
        });
    }
    
    // Botón cerrar modal del Agent
    const btnCloseAgentModal = document.getElementById('btnCloseAgentModal');
    if (btnCloseAgentModal) {
        btnCloseAgentModal.addEventListener('click', closeAgentInstallModal);
    }
    
    // Tabs de instrucciones
    document.querySelectorAll('.agent-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            const os = this.getAttribute('data-os');
            switchAgentTab(os);
        });
    });
    
    // Botón verificar desde modal
    const btnVerifyAgentInstall = document.getElementById('btnVerifyAgentInstall');
    if (btnVerifyAgentInstall) {
        btnVerifyAgentInstall.addEventListener('click', verifyAgentFromModal);
    }
    
    // Cerrar modal al hacer clic fuera
    const agentInstallModal = document.getElementById('agentInstallModal');
    if (agentInstallModal) {
        agentInstallModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeAgentInstallModal();
            }
        });
    }
    
    // Detectar SO del usuario y mostrar tab correspondiente
    const userAgent = navigator.userAgent.toLowerCase();
    if (userAgent.includes('win')) {
        switchAgentTab('windows');
    } else if (userAgent.includes('mac')) {
        switchAgentTab('mac');
    } else {
        switchAgentTab('linux');
    }
});
