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

// Web Serial API
let serialPort = null;
let serialReader = null;
let serialWriter = null;
let readBuffer = '';

// Estado de upload (anti-doble-click)
let isUploading = false;

// Web Serial para Upload
let uploadPort = null;
let availablePorts = []; // Puertos Web Serial disponibles

// Proyectos
let currentProjectId = null;

// ============================================
// ARDUINO UPLOADER - Protocolo STK500
// ============================================

/**
 * Fuerza un reset robusto del bootloader antes del handshake STK500.
 * Soluciona el problema de "Recibido []" cuando el bootloader no responde.
 * 
 * @param {SerialPort} port - Puerto Web Serial
 * @param {number} bootloaderBaud - Baudrate del bootloader (ej: 115200)
 * @param {Function} log - Función de logging opcional
 * @returns {Promise<boolean>} - true si el reset fue exitoso
 */
async function forceBootloaderReset(port, bootloaderBaud = 115200, log = console.log) {
    try {
        log('[RESET] Iniciando reset robusto del bootloader...');
        
        // ========================================
        // 1. CERRAR CUALQUIER READER/WRITER ACTIVO
        // ========================================
        if (port.readable) {
            try {
                const reader = port.readable.getReader();
                await reader.cancel().catch(() => {});
                reader.releaseLock();
                log('[RESET] Reader cancelado y liberado');
            } catch (e) {
                log(`[RESET] No había reader activo o error: ${e.message}`);
            }
        }
        
        if (port.writable) {
            try {
                const writer = port.writable.getWriter();
                writer.releaseLock();
                log('[RESET] Writer liberado');
            } catch (e) {
                log(`[RESET] No había writer activo o error: ${e.message}`);
            }
        }
        
        // ========================================
        // 2. CERRAR PUERTO COMPLETAMENTE
        // ========================================
        try {
            if (port.readable || port.writable) {
                await port.close();
                log('[RESET] Puerto cerrado');
            }
        } catch (e) {
            log(`[RESET] Puerto ya cerrado o error: ${e.message}`);
        }
        
        // Pequeña espera después de cerrar
        await new Promise(r => setTimeout(r, 100));
        
        // ========================================
        // 3. ABRIR A 1200 BAUD (TRIGGER DE RESET)
        // ========================================
        // 1200 baud es un trigger especial para algunos bootloaders (Leonardo, etc.)
        // y también funciona para activar el auto-reset en muchos Arduinos
        try {
            log('[RESET] Abriendo puerto a 1200 baud (trigger de reset)...');
            await port.open({ baudRate: 1200, dataBits: 8, stopBits: 1, parity: 'none' });
            log('[RESET] Puerto abierto a 1200 baud');
            
            // ========================================
            // 4. TOGGLE DTR/RTS PARA RESET
            // ========================================
            if (port.setSignals) {
                log('[RESET] Ejecutando secuencia DTR/RTS...');
                
                // Paso 1: Ambas señales LOW
                await port.setSignals({ dataTerminalReady: false, requestToSend: false });
                log('[RESET] DTR=LOW, RTS=LOW');
                await new Promise(r => setTimeout(r, 50));
                
                // Paso 2: Ambas señales HIGH (genera pulso de reset)
                await port.setSignals({ dataTerminalReady: true, requestToSend: true });
                log('[RESET] DTR=HIGH, RTS=HIGH');
                await new Promise(r => setTimeout(r, 50));
                
                // Paso 3: Ambas señales LOW otra vez
                await port.setSignals({ dataTerminalReady: false, requestToSend: false });
                log('[RESET] DTR=LOW, RTS=LOW');
                await new Promise(r => setTimeout(r, 50));
            } else {
                log('[RESET] setSignals no disponible, saltando toggle DTR/RTS');
            }
            
            // ========================================
            // 5. CERRAR PUERTO OTRA VEZ
            // ========================================
            await port.close();
            log('[RESET] Puerto cerrado después del reset');
            
        } catch (e) {
            log(`[RESET] Error durante reset a 1200 baud: ${e.message}`);
            // Intentar cerrar por si quedó abierto
            try { await port.close(); } catch (e2) {}
        }
        
        // ========================================
        // 6. ESPERAR A QUE EL BOOTLOADER INICIE
        // ========================================
        const bootloaderWait = 350; // ms - tiempo típico de inicio del bootloader
        log(`[RESET] Esperando ${bootloaderWait}ms para que el bootloader inicie...`);
        await new Promise(r => setTimeout(r, bootloaderWait));
        
        // ========================================
        // 7. REABRIR AL BAUD DEL BOOTLOADER
        // ========================================
        log(`[RESET] Reabriendo puerto a ${bootloaderBaud} baud...`);
        await port.open({ 
            baudRate: bootloaderBaud, 
            dataBits: 8, 
            stopBits: 1, 
            parity: 'none',
            flowControl: 'none'
        });
        log(`[RESET] Puerto abierto a ${bootloaderBaud} baud`);
        
        // Espera adicional para estabilizar
        const stabilizeWait = 200; // ms
        log(`[RESET] Esperando ${stabilizeWait}ms para estabilizar...`);
        await new Promise(r => setTimeout(r, stabilizeWait));
        
        log('[RESET] ✓ Reset del bootloader completado');
        return true;
        
    } catch (error) {
        log(`[RESET] ✗ Error durante reset: ${error.message}`);
        // Intentar cerrar el puerto por si quedó en mal estado
        try { await port.close(); } catch (e) {}
        return false;
    }
}

class ArduinoUploader {
    constructor() {
        this.port = null;
        this.reader = null;
        this.writer = null;
        this.readable = null;
        this.writable = null;
        this.logFunc = console.log;
    }
    
    /**
     * Configura la función de logging
     */
    setLogger(logFunc) {
        this.logFunc = logFunc || console.log;
    }

    // Constantes del protocolo STK500
    static STK = {
        OK: 0x10,
        INSYNC: 0x14,
        CRC_EOP: 0x20,
        GET_SYNC: 0x30,
        GET_PARAMETER: 0x41,
        ENTER_PROGMODE: 0x50,
        LEAVE_PROGMODE: 0x51,
        LOAD_ADDRESS: 0x55,
        PROG_PAGE: 0x64,
        READ_SIGN: 0x75,
    };
    
    // Baudrates a probar para el bootloader (Optiboot vs bootloader antiguo)
    static BOOTLOADER_BAUDS = [115200, 57600];

    /**
     * Conecta al Arduino con auto-fallback de baudrate.
     * Prueba cada baudrate en orden hasta encontrar uno que funcione.
     */
    async connect(port, preferredBaud = 115200) {
        this.port = port;
        
        // Lista de baudrates a probar, empezando por el preferido
        const baudsToTry = [preferredBaud, ...ArduinoUploader.BOOTLOADER_BAUDS.filter(b => b !== preferredBaud)];
        
        this.logFunc('[CONNECT] Iniciando conexión con auto-fallback de baudrate...');
        this.logFunc(`[CONNECT] Baudrates a probar: ${baudsToTry.join(', ')}`);
        
        let lastError = null;
        
        for (const baud of baudsToTry) {
            this.logFunc(`[CONNECT] ═══════════════════════════════════════`);
            this.logFunc(`[CONNECT] Probando baud ${baud}...`);
            
            try {
                // ========================================
                // 1. RESET ROBUSTO DEL BOOTLOADER
                // ========================================
                this.logFunc(`[CONNECT] Ejecutando reset robusto a ${baud} baud...`);
                const resetOk = await forceBootloaderReset(port, baud, this.logFunc);
                
                if (!resetOk) {
                    this.logFunc(`[CONNECT] Reset falló a ${baud} baud, probando siguiente...`);
                    continue;
                }
                
                // ========================================
                // 2. VERIFICAR QUE EL PUERTO ESTÉ ABIERTO
                // ========================================
                if (!this.port.readable || !this.port.writable) {
                    this.logFunc(`[CONNECT] Abriendo puerto a ${baud} baud...`);
                    await this.port.open({ 
                        baudRate: baud, 
                        dataBits: 8, 
                        stopBits: 1, 
                        parity: 'none',
                        flowControl: 'none'
                    });
                }
                
                // Obtener reader/writer
                this.writable = this.port.writable;
                this.readable = this.port.readable;
                this.writer = this.writable.getWriter();
                this.reader = this.readable.getReader();
                
                // ========================================
                // 3. SYNC RÁPIDO (5 intentos, 150ms timeout)
                // ========================================
                this.logFunc(`[CONNECT] Probando sync STK500 a ${baud} baud (5 intentos rápidos)...`);
                const syncOk = await this.tryQuickSync(5, 150);
                
                if (syncOk) {
                    this.baudRate = baud;
                    this.logFunc(`[CONNECT] ✓ Sync OK a ${baud} baud!`);
                    this.logFunc(`[CONNECT] ✓ Conectado y listo para comunicación STK500`);
                    return; // Éxito!
                }
                
                // Sync falló, limpiar y probar siguiente baudrate
                this.logFunc(`[CONNECT] ✗ Sync falló a ${baud} baud`);
                await this.cleanupForRetry();
                
            } catch (error) {
                this.logFunc(`[CONNECT] ✗ Error a ${baud} baud: ${error.message}`);
                lastError = error;
                await this.cleanupForRetry();
            }
        }
        
        // Ningún baudrate funcionó
        throw new Error(`No se pudo conectar al bootloader. Probados: ${baudsToTry.join(', ')}. ¿Está el Arduino conectado correctamente?`);
    }
    
    /**
     * Limpia la conexión para poder reintentar con otro baudrate
     */
    async cleanupForRetry() {
        try {
            if (this.reader) {
                try { await this.reader.cancel(); } catch (e) {}
                try { this.reader.releaseLock(); } catch (e) {}
                this.reader = null;
            }
            if (this.writer) {
                try { this.writer.releaseLock(); } catch (e) {}
                this.writer = null;
            }
            if (this.port && (this.port.readable || this.port.writable)) {
                try { await this.port.close(); } catch (e) {}
            }
            this.readable = null;
            this.writable = null;
        } catch (e) {
            // Ignorar errores de limpieza
        }
        // Pequeña espera antes de reintentar
        await new Promise(r => setTimeout(r, 100));
    }
    
    /**
     * Intenta sync rápido con el bootloader
     * @param {number} maxAttempts - Número máximo de intentos
     * @param {number} timeout - Timeout por intento en ms
     * @returns {Promise<boolean>} - true si sync exitoso
     */
    async tryQuickSync(maxAttempts = 5, timeout = 150) {
        // Toggle DTR rápido para reforzar el reset
        if (this.port.setSignals) {
            try {
                await this.port.setSignals({ dataTerminalReady: true, requestToSend: false });
                await new Promise(r => setTimeout(r, 30));
                await this.port.setSignals({ dataTerminalReady: false, requestToSend: false });
                await new Promise(r => setTimeout(r, 50));
            } catch (e) {
                // Ignorar errores de setSignals
            }
        }
        
        // Limpiar buffer
        try {
            while (true) {
                const { value, done } = await Promise.race([
                    this.reader.read(),
                    new Promise(r => setTimeout(() => r({ done: true }), 30))
                ]);
                if (done || !value || value.length === 0) break;
            }
        } catch (e) {}
        
        // Intentar sync
        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            try {
                await this.send([ArduinoUploader.STK.GET_SYNC, ArduinoUploader.STK.CRC_EOP]);
                const response = await this.receive(2, timeout);
                
                const respHex = Array.from(response).map(b => '0x' + b.toString(16).padStart(2, '0')).join(', ');
                this.logFunc(`[SYNC] Intento ${attempt + 1}/${maxAttempts}: [${respHex}]`);
                
                if (response.length >= 2 && 
                    response[0] === ArduinoUploader.STK.INSYNC && 
                    response[1] === ArduinoUploader.STK.OK) {
                    return true;
                }
            } catch (e) {
                this.logFunc(`[SYNC] Intento ${attempt + 1}/${maxAttempts}: timeout`);
            }
            
            await new Promise(r => setTimeout(r, 30));
        }
        
        return false;
    }

    async disconnect() {
        this.logFunc('[DISCONNECT] Iniciando limpieza de conexión...');
        
        try {
            // 1. Cancelar y liberar reader
            if (this.reader) {
                try {
                    await this.reader.cancel();
                    this.logFunc('[DISCONNECT] Reader cancelado');
                } catch (e) {
                    this.logFunc(`[DISCONNECT] Error cancelando reader: ${e.message}`);
                }
                try {
                    this.reader.releaseLock();
                    this.logFunc('[DISCONNECT] Reader lock liberado');
                } catch (e) {
                    this.logFunc(`[DISCONNECT] Error liberando reader lock: ${e.message}`);
                }
                this.reader = null;
            }
            
            // 2. Cerrar y liberar writer
            if (this.writer) {
                try {
                    this.writer.releaseLock();
                    this.logFunc('[DISCONNECT] Writer lock liberado');
                } catch (e) {
                    this.logFunc(`[DISCONNECT] Error liberando writer lock: ${e.message}`);
                }
                this.writer = null;
            }
            
            // 3. Cerrar puerto
            if (this.port) {
                try {
                    if (this.port.readable || this.port.writable) {
                        await this.port.close();
                        this.logFunc('[DISCONNECT] Puerto cerrado');
                    }
                } catch (e) {
                    this.logFunc(`[DISCONNECT] Error cerrando puerto: ${e.message}`);
                }
            }
            
            // Limpiar referencias
            this.readable = null;
            this.writable = null;
            
            this.logFunc('[DISCONNECT] ✓ Limpieza completada');
            
        } catch (e) {
            this.logFunc(`[DISCONNECT] ✗ Error crítico durante limpieza: ${e.message}`);
            // Forzar limpieza de referencias aunque haya error
            this.reader = null;
            this.writer = null;
            this.readable = null;
            this.writable = null;
        }
    }

    async send(data) {
        await this.writer.write(new Uint8Array(data));
    }

    async receive(length, timeout = 1000) {
        const result = [];
        const deadline = Date.now() + timeout;
        
        while (result.length < length && Date.now() < deadline) {
            try {
                const { value, done } = await Promise.race([
                    this.reader.read(),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('timeout')), Math.max(100, deadline - Date.now()))
                    )
                ]);
                if (done) break;
                if (value) result.push(...value);
            } catch (e) {
                if (e.message !== 'timeout') throw e;
                break;
            }
        }
        return new Uint8Array(result.slice(0, length));
    }

    /**
     * Sincroniza con el bootloader.
     * Nota: La sincronización principal ya se hace en connect() con fallback de baudrate.
     * Este método es para verificar/re-sincronizar si es necesario.
     */
    async sync() {
        this.logFunc('[SYNC] Verificando sincronización con bootloader...');
        
        // La sincronización ya se hizo en connect(), solo verificamos
        // Usamos tryQuickSync para verificar rápidamente
        const syncOk = await this.tryQuickSync(3, 200);
        
        if (syncOk) {
            this.logFunc('[SYNC] ✓ Sincronización verificada');
            return true;
        }
        
        // Si falló, intentar con más intentos
        this.logFunc('[SYNC] Reintentando sincronización (10 intentos)...');
        const retryOk = await this.tryQuickSync(10, 300);
        
        if (retryOk) {
            this.logFunc('[SYNC] ✓ Sincronización recuperada');
            return true;
        }
        
        this.logFunc('[SYNC] ✗ No se pudo sincronizar');
        throw new Error('No se pudo sincronizar con el bootloader. Verifica que el Arduino esté conectado.');
    }

    async enterProgramMode() {
        await this.send([ArduinoUploader.STK.ENTER_PROGMODE, ArduinoUploader.STK.CRC_EOP]);
        const response = await this.receive(2);
        if (response.length < 2 || response[0] !== ArduinoUploader.STK.INSYNC || response[1] !== ArduinoUploader.STK.OK) {
            throw new Error('Error entrando en modo programación');
        }
    }

    async loadAddress(address) {
        const addr = address >> 1; // Word address
        await this.send([
            ArduinoUploader.STK.LOAD_ADDRESS,
            addr & 0xFF,
            (addr >> 8) & 0xFF,
            ArduinoUploader.STK.CRC_EOP
        ]);
        const response = await this.receive(2);
        if (response.length < 2 || response[0] !== ArduinoUploader.STK.INSYNC || response[1] !== ArduinoUploader.STK.OK) {
            throw new Error('Error cargando dirección');
        }
    }

    async programPage(data) {
        const cmd = [
            ArduinoUploader.STK.PROG_PAGE,
            (data.length >> 8) & 0xFF,
            data.length & 0xFF,
            0x46, // 'F' for Flash
            ...data,
            ArduinoUploader.STK.CRC_EOP
        ];
        await this.send(cmd);
        const response = await this.receive(2, 5000);
        if (response.length < 2 || response[0] !== ArduinoUploader.STK.INSYNC || response[1] !== ArduinoUploader.STK.OK) {
            throw new Error('Error programando página');
        }
    }

    async leaveProgramMode() {
        await this.send([ArduinoUploader.STK.LEAVE_PROGMODE, ArduinoUploader.STK.CRC_EOP]);
        await this.receive(2);
    }

    /**
     * Parsea archivo Intel HEX
     * Retorna solo los bytes reales del programa, sin espacios vacíos
     */
    parseHex(hexString) {
        const segments = []; // Array de {address, data}
        let baseAddress = 0;
        let currentSegment = null;
        
        for (const line of hexString.split('\n')) {
            const trimmed = line.trim();
            if (!trimmed.startsWith(':')) continue;
            
            const bytes = [];
            for (let i = 1; i < trimmed.length; i += 2) {
                const byte = parseInt(trimmed.substr(i, 2), 16);
                if (!isNaN(byte)) bytes.push(byte);
            }
            
            if (bytes.length < 4) continue;
            
            const count = bytes[0];
            const address = (bytes[1] << 8) | bytes[2];
            const type = bytes[3];
            
            if (type === 0x00) { // Data record
                const fullAddress = baseAddress + address;
                const recordData = bytes.slice(4, 4 + count);
                
                // Si es continuación del segmento actual
                if (currentSegment && 
                    fullAddress === currentSegment.address + currentSegment.data.length) {
                    currentSegment.data.push(...recordData);
                } else {
                    // Nuevo segmento
                    if (currentSegment) segments.push(currentSegment);
                    currentSegment = { address: fullAddress, data: [...recordData] };
                }
            } else if (type === 0x02) { // Extended Segment Address
                if (bytes.length >= 6) {
                    baseAddress = ((bytes[4] << 8) | bytes[5]) << 4;
                }
            } else if (type === 0x04) { // Extended Linear Address
                if (bytes.length >= 6) {
                    baseAddress = ((bytes[4] << 8) | bytes[5]) << 16;
                }
            } else if (type === 0x01) { // EOF
                break;
            }
        }
        
        if (currentSegment) segments.push(currentSegment);
        
        if (segments.length === 0) {
            throw new Error('Archivo HEX vacío o inválido');
        }
        
        // Para Arduino, normalmente solo hay un segmento continuo desde 0x0000
        // Combinar todos los segmentos en uno solo
        const allData = [];
        let startAddress = segments[0].address;
        
        for (const seg of segments) {
            // Llenar gaps pequeños (< 256 bytes) con 0xFF
            const gap = seg.address - (startAddress + allData.length);
            if (gap > 0 && gap < 256) {
                for (let i = 0; i < gap; i++) allData.push(0xFF);
            }
            allData.push(...seg.data);
        }
        
        console.log(`HEX parseado: ${allData.length} bytes desde 0x${startAddress.toString(16)}`);
        
        return { data: new Uint8Array(allData), startAddress };
    }

    /**
     * Sube el código al Arduino
     */
    async upload(hexContent, onProgress = () => {}) {
        const pageSize = 128; // Arduino UNO/Nano
        
        onProgress('Parseando archivo HEX...', 5);
        const { data: firmware, startAddress } = this.parseHex(hexContent);
        
        onProgress(`Firmware: ${firmware.length} bytes`, 10);
        
        try {
            onProgress('Sincronizando con bootloader...', 15);
            await this.sync();
            
            onProgress('Entrando en modo programación...', 20);
            await this.enterProgramMode();
            
            const totalPages = Math.ceil(firmware.length / pageSize);
            let pagesWritten = 0;
            
            for (let i = 0; i < firmware.length; i += pageSize) {
                const page = firmware.slice(i, Math.min(i + pageSize, firmware.length));
                const paddedPage = new Uint8Array(pageSize);
                paddedPage.fill(0xFF); // Fill with 0xFF (erased flash value)
                paddedPage.set(page);
                
                await this.loadAddress(startAddress + i);
                await this.programPage(paddedPage);
                
                pagesWritten++;
                const progress = 20 + Math.floor((pagesWritten / totalPages) * 70);
                onProgress(`Programando... ${Math.floor((i + pageSize) / firmware.length * 100)}%`, progress);
            }
            
            onProgress('Finalizando...', 95);
            await this.leaveProgramMode();
            
            onProgress('¡Completado!', 100);
            
        } catch (error) {
            throw error;
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
    
    // Verificar Web Serial API
    if ('serial' in navigator) {
        logToConsole('✓ Web Serial API disponible - Puertos de tu PC', 'success');
        refreshPorts();
        startPortMonitoring();
    } else {
        logToConsole('⚠️ Web Serial API NO disponible', 'error');
        logToConsole('Requiere: Chrome/Edge/Opera + HTTPS', 'warning');
        showToast('Web Serial no disponible. Usa HTTPS con Chrome/Edge/Opera.', 'error');
        
        // Mostrar mensaje en el selector de puertos
        const select = document.getElementById('portSelect');
        select.innerHTML = '<option value="">⚠️ Web Serial no disponible</option>';
    }
    
    logToConsole('MAX-IDE v2.0 - Modo Web Serial', 'info');
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
    document.getElementById('btnAddPort').addEventListener('click', requestNewPort);
    
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
        document.getElementById('btnCloseProjects').addEventListener('click', () => {
            projectsModal.style.display = 'none';
        });
        document.getElementById('btnCreateNewProject').addEventListener('click', () => {
            projectsModal.style.display = 'none';
            if (createProjectModal) createProjectModal.style.display = 'flex';
        });
        document.getElementById('btnCancelCreateProject').addEventListener('click', () => {
            if (createProjectModal) createProjectModal.style.display = 'none';
        });
        document.getElementById('btnConfirmCreateProject').addEventListener('click', createNewProject);
        document.getElementById('btnCloseCreateProject').addEventListener('click', () => {
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
        if (currentPort !== '' && availablePorts[parseInt(currentPort)]) {
            const port = availablePorts[parseInt(currentPort)];
            const info = port.getInfo();
            let deviceType = 'Desconocido';
            let details = [];
            
            // Identificar tipo de dispositivo
            if (info.usbVendorId === 0x2341 || info.usbVendorId === 0x2A03) {
                deviceType = 'Arduino Oficial';
            } else if (info.usbVendorId === 0x1A86) {
                deviceType = 'CH340 (clon típico)';
            } else if (info.usbVendorId === 0x0403) {
                deviceType = 'FTDI';
            } else if (info.usbVendorId === 0x10C4) {
                deviceType = 'CP210x';
            }
            
            if (info.usbVendorId) {
                details.push(`VID: 0x${info.usbVendorId.toString(16).toUpperCase()}`);
            }
            if (info.usbProductId) {
                details.push(`PID: 0x${info.usbProductId.toString(16).toUpperCase()}`);
            }
            if (info.serialNumber) {
                details.push(`S/N: ${info.serialNumber}`);
            }
            
            logToConsole(`Puerto seleccionado: ${deviceType}`, 'info');
            if (details.length > 0) {
                logToConsole(`  ${details.join(' | ')}`, 'info');
            }
            
            // Advertencia si es CH340 y está seleccionado UNO
            if (info.usbVendorId === 0x1A86 && currentBoard === 'arduino:avr:uno') {
                showBoardSuggestion('CH340 detectado. Si el upload falla, prueba con "Arduino Nano (Old Bootloader)".', 'arduino:avr:nano');
            }
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
 * Verifica si hay cambios en los puertos conectados (Web Serial API)
 */
async function checkForNewPorts() {
    try {
        if (!('serial' in navigator)) {
            return; // Web Serial no disponible
        }
        
        const currentPorts = await navigator.serial.getPorts();
        
        // Detectar cambios en la cantidad de puertos autorizados
        if (currentPorts.length !== lastKnownPorts.length) {
            // Actualizar lista
            availablePorts = currentPorts;
            await refreshPorts();
            
            if (currentPorts.length > lastKnownPorts.length) {
                showToast(`Nuevo puerto disponible`, 'success');
                logToConsole(`🔌 Cambio detectado en puertos`, 'info');
            } else if (currentPorts.length < lastKnownPorts.length) {
                // Verificar si el puerto en uso fue desconectado
                const selectedIndex = parseInt(currentPort);
                if (!isNaN(selectedIndex) && !currentPorts[selectedIndex]) {
                    currentPort = '';
                    updateConnectionStatus();
                    showToast(`Puerto desconectado`, 'warning');
                    logToConsole(`⚠️ Puerto desconectado`, 'warning');
                }
            }
        }
        
        lastKnownPorts = currentPorts;
        
    } catch (error) {
        // Silenciar errores de polling
    }
}

/**
 * Auto-selecciona un puerto (para compatibilidad con servidor)
 */
function autoSelectPort(port) {
    const select = document.getElementById('portSelect');
    const serialSelect = document.getElementById('serialPortSelect');
    
    if (port.device) {
        select.value = port.device;
        if (serialSelect) serialSelect.value = port.device;
        currentPort = port.device;
        updateConnectionStatus();
    }
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
        // Verificar soporte de Web Serial API
        if (!('serial' in navigator)) {
            select.innerHTML = '<option value="">Web Serial no disponible</option>';
            if (serialSelect) serialSelect.innerHTML = '<option value="">Web Serial no disponible</option>';
            logToConsole('⚠️ Web Serial API no disponible. Usa Chrome, Edge u Opera.', 'warning');
            btn.innerHTML = '🔄';
            return;
        }
        
        // Obtener puertos ya autorizados (del cliente)
        availablePorts = await navigator.serial.getPorts();
        
        if (availablePorts.length > 0) {
            const optionsHtml = '<option value="">Seleccionar puerto...</option>' +
                availablePorts.map((port, index) => {
                    const info = port.getInfo();
                    let deviceType = 'Desconocido';
                    let metadata = [];
                    
                    // Identificar tipo de dispositivo por VID
                    if (info.usbVendorId === 0x2341 || info.usbVendorId === 0x2A03) {
                        deviceType = 'Arduino Oficial';
                    } else if (info.usbVendorId === 0x1A86) {
                        deviceType = 'CH340 (clon típico)';
                    } else if (info.usbVendorId === 0x0403) {
                        deviceType = 'FTDI';
                    } else if (info.usbVendorId === 0x10C4) {
                        deviceType = 'CP210x';
                    }
                    
                    // Agregar metadata
                    if (info.usbVendorId) {
                        metadata.push(`VID:0x${info.usbVendorId.toString(16).toUpperCase()}`);
                    }
                    if (info.usbProductId) {
                        metadata.push(`PID:0x${info.usbProductId.toString(16).toUpperCase()}`);
                    }
                    if (info.serialNumber) {
                        metadata.push(`S/N:${info.serialNumber.substring(0, 8)}`);
                    }
                    
                    const metadataStr = metadata.length > 0 ? ` [${metadata.join(', ')}]` : '';
                    const label = `${deviceType}${metadataStr}`;
                    
                    return `<option value="${index}" title="${info.serialNumber || 'Sin S/N'}">${label}</option>`;
                }).join('');
            
            select.innerHTML = optionsHtml;
            if (serialSelect) serialSelect.innerHTML = optionsHtml;
            
            logToConsole(`${availablePorts.length} puerto(s) disponible(s) en tu PC`, 'success');
            
            // Auto-seleccionar si solo hay uno
            if (availablePorts.length === 1) {
                select.value = '0';
                if (serialSelect) serialSelect.value = '0';
                currentPort = '0';
                updateConnectionStatus();
            }
        } else {
            select.innerHTML = '<option value="">Haz clic en + para agregar puerto</option>';
            if (serialSelect) serialSelect.innerHTML = '<option value="">Haz clic en + para agregar puerto</option>';
            logToConsole('No hay puertos autorizados. Haz clic en el botón + para agregar uno.', 'info');
        }
    } catch (error) {
        logToConsole('Error al buscar puertos: ' + error.message, 'error');
    }
    
    btn.innerHTML = '🔄';
}

/**
 * Solicita al usuario seleccionar un nuevo puerto serial (del cliente)
 */
async function requestNewPort() {
    console.log('requestNewPort() llamado');
    logToConsole('Solicitando puerto serial...', 'info');
    
    if (!('serial' in navigator)) {
        const msg = 'Web Serial API no disponible. Requiere HTTPS + Chrome/Edge/Opera.';
        showToast(msg, 'error');
        logToConsole(msg, 'error');
        alert(msg);
        return;
    }
    
    // Verificar contexto seguro
    if (!window.isSecureContext) {
        const msg = 'Web Serial requiere HTTPS. Configura SSL en el servidor.';
        showToast(msg, 'error');
        logToConsole(msg, 'error');
        alert(msg);
        return;
    }
    
    try {
        // Solicitar nuevo puerto al usuario - esto abre el diálogo del navegador
        logToConsole('Abriendo selector de puertos del navegador...', 'info');
        const port = await navigator.serial.requestPort();
        
        logToConsole('Puerto seleccionado por el usuario', 'success');
        
        // Agregar a la lista si no existe
        if (!availablePorts.includes(port)) {
            availablePorts.push(port);
        }
        
        // Actualizar la lista de puertos
        await refreshPorts();
        
        // Seleccionar el nuevo puerto
        const index = availablePorts.indexOf(port);
        if (index >= 0) {
            document.getElementById('portSelect').value = index.toString();
            currentPort = index.toString();
            updateConnectionStatus();
            showToast('✓ Puerto agregado correctamente', 'success');
            logToConsole('Puerto agregado y seleccionado', 'success');
        }
    } catch (error) {
        console.error('Error en requestNewPort:', error);
        if (error.name === 'NotFoundError') {
            logToConsole('Selección de puerto cancelada', 'info');
        } else if (error.name === 'SecurityError') {
            const msg = 'Error de seguridad. Verifica que uses HTTPS.';
            showToast(msg, 'error');
            logToConsole(msg, 'error');
        } else {
            showToast('Error: ' + error.message, 'error');
            logToConsole('Error: ' + error.message, 'error');
        }
    }
}

function updateConnectionStatus() {
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('statusText');
    
    // Para el estado de conexión, verificar si hay puerto serial o puerto para subir código
    if (isSerialConnected) {
        dot.classList.remove('disconnected');
        text.textContent = 'Serial: Conectado';
    } else if (currentPort !== '' && availablePorts[parseInt(currentPort)]) {
        dot.classList.remove('disconnected');
        const info = availablePorts[parseInt(currentPort)].getInfo();
        let label = `Puerto ${parseInt(currentPort) + 1}`;
        if (info.usbVendorId === 0x2341 || info.usbVendorId === 0x2A03) {
            label = 'Arduino';
        } else if (info.usbVendorId === 0x1A86) {
            label = 'CH340';
        } else if (info.usbVendorId === 0x0403) {
            label = 'FTDI';
        }
        text.textContent = `Puerto: ${label}`;
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
    
    // Anti-doble-click: si ya estamos subiendo, ignorar
    if (isUploading) {
        console.log('[UPLOAD] Ya hay una subida en progreso, ignorando click');
        return;
    }
    
    if (!code.trim()) {
        showToast('No hay código para subir', 'warning');
        return;
    }
    
    // Verificar Web Serial API
    if (!('serial' in navigator)) {
        showToast('Web Serial API no disponible. Usa Chrome, Edge u Opera.', 'error');
        return;
    }
    
    // Verificar que hay un puerto seleccionado
    let selectedPort = null;
    const portIndex = parseInt(currentPort);
    
    if (!isNaN(portIndex) && availablePorts[portIndex]) {
        selectedPort = availablePorts[portIndex];
    } else {
        // Intentar solicitar un puerto
        try {
            selectedPort = await navigator.serial.requestPort();
            if (!availablePorts.includes(selectedPort)) {
                availablePorts.push(selectedPort);
            }
            await refreshPorts();
        } catch (error) {
            if (error.name === 'NotFoundError') {
                showToast('Selecciona un puerto para continuar', 'warning');
            } else {
                showToast('Error: ' + error.message, 'error');
            }
            return;
        }
    }
    
    // ========================================
    // VERIFICAR Y CERRAR MONITOR SERIAL
    // ========================================
    if (isSerialConnected) {
        logToConsole('[UPLOAD] Monitor serial conectado -> solicitando cierre...', 'warning');
        
        // Mostrar confirmación al usuario
        const confirmClose = confirm(
            '⚠️ Para subir código debo cerrar el Monitor Serial.\n\n' +
            'El puerto está siendo usado por el monitor y no puede compartirse.\n\n' +
            '¿Cerrar el Monitor Serial y continuar con la subida?'
        );
        
        if (!confirmClose) {
            logToConsole('[UPLOAD] Subida cancelada por el usuario', 'info');
            showToast('Subida cancelada', 'info');
            return;
        }
        
        // Cerrar el monitor serial
        logToConsole('[UPLOAD] Cerrando monitor serial...', 'info');
        btn.disabled = true;
        btn.innerHTML = '<span class="loading"></span> Cerrando serial...';
        
        const disconnected = await disconnectSerial(false);
        
        if (!disconnected) {
            logToConsole('[UPLOAD] ✗ Error al cerrar monitor serial', 'error');
            showToast('Error al cerrar el monitor serial', 'error');
            btn.disabled = false;
            btn.innerHTML = '<span>🚀</span><span>Subir</span>';
            return;
        }
        
        logToConsole('[UPLOAD] ✓ Monitor serial cerrado OK', 'success');
        
        // Espera adicional para asegurar que el puerto esté libre
        await new Promise(r => setTimeout(r, 500));
    }
    
    // ========================================
    // INICIAR PROCESO DE SUBIDA
    // ========================================
    isUploading = true;
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> Compilando...';
    logToConsole('[UPLOAD] Iniciando compilación en servidor...', 'info');
    
    const uploader = new ArduinoUploader();
    
    // Configurar logger para que todos los mensajes del uploader vayan a la consola
    uploader.setLogger((msg) => {
        logToConsole(msg, 'info');
        console.log(msg);
    });
    
    try {
        // 1. Compilar en el servidor y obtener HEX
        logToConsole('[UPLOAD] Llamando API /compile-download/...', 'info');
        const compileResponse = await fetch('/api/compile-download/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, board: currentBoard })
        });
        
        const compileData = await compileResponse.json();
        
        if (!compileData.success) {
            logToConsole('[UPLOAD] ✗ Error de compilación:', 'error');
            logToConsole(compileData.error || 'Error desconocido', 'error');
            showToast('Error de compilación', 'error');
            isUploading = false;
            btn.disabled = false;
            btn.innerHTML = '<span>🚀</span><span>Subir</span>';
            return;
        }
        
        if (!compileData.hex_file) {
            logToConsole('[UPLOAD] ✗ No se generó archivo HEX', 'error');
            showToast('Error: No se generó archivo HEX', 'error');
            isUploading = false;
            btn.disabled = false;
            btn.innerHTML = '<span>🚀</span><span>Subir</span>';
            return;
        }
        
        logToConsole('[UPLOAD] ✓ Compilación exitosa', 'success');
        
        // 2. Decodificar el HEX
        const hexContent = atob(compileData.hex_file);
        
        // 3. Subir directamente usando Web Serial API
        btn.innerHTML = '<span class="loading"></span> Conectando...';
        logToConsole('[UPLOAD] Preparando conexión al Arduino...', 'info');
        
        // Determinar baudrate según la placa
        let uploadBaud = 115200;
        if (currentBoard.includes('uno') || currentBoard.includes('nano')) {
            uploadBaud = 115200;
        } else if (currentBoard.includes('mega')) {
            uploadBaud = 115200;
        } else if (currentBoard.includes('leonardo')) {
            // Leonardo usa CDC, diferente protocolo
            showToast('Arduino Leonardo requiere modo especial (no soportado aún)', 'warning');
            isUploading = false;
            btn.disabled = false;
            btn.innerHTML = '<span>🚀</span><span>Subir</span>';
            return;
        }
        
        logToConsole(`[UPLOAD] Conectando a ${uploadBaud} baud con reset robusto...`, 'info');
        btn.innerHTML = '<span class="loading"></span> Reset...';
        
        await uploader.connect(selectedPort, uploadBaud);
        
        btn.innerHTML = '<span class="loading"></span> Subiendo...';
        await uploader.upload(hexContent, (msg, progress) => {
            logToConsole(`[UPLOAD] ${msg}`, 'info');
            btn.innerHTML = `<span class="loading"></span> ${progress}%`;
        });
        
        logToConsole('[UPLOAD] ✓ ¡Código subido exitosamente!', 'success');
        showToast('¡Código subido exitosamente!', 'success');
        
    } catch (error) {
        logToConsole('[UPLOAD] ✗ Error: ' + error.message, 'error');
        showToast('Error: ' + error.message, 'error');
    } finally {
        // ========================================
        // CLEANUP ROBUSTO (siempre se ejecuta)
        // ========================================
        logToConsole('[UPLOAD] Ejecutando limpieza...', 'info');
        try {
            await uploader.disconnect();
        } catch (e) {
            logToConsole(`[UPLOAD] Error durante limpieza: ${e.message}`, 'warning');
        }
        
        isUploading = false;
        btn.disabled = false;
        btn.innerHTML = '<span>🚀</span><span>Subir</span>';
    }
}

// ============================================
// MONITOR SERIAL
// ============================================

function openSerialMonitor() {
    document.getElementById('serialModal').classList.add('active');
    
    // Verificar soporte de Web Serial API
    if (!('serial' in navigator)) {
        addSerialLine('⚠️ Web Serial API no está disponible en este navegador.', 'system');
        addSerialLine('Por favor, usa Chrome, Edge u Opera para acceder al monitor serial.', 'system');
        logToConsole('Web Serial API no disponible en este navegador', 'warning');
        document.getElementById('btnSerialConnect').disabled = true;
    } else {
        document.getElementById('btnSerialConnect').disabled = false;
        // Mostrar información sobre puertos previamente seleccionados
        navigator.serial.getPorts().then(ports => {
            if (ports.length > 0) {
                addSerialLine(`ℹ️ ${ports.length} puerto(s) previamente seleccionado(s).`, 'system');
                addSerialLine('Haz clic en "Conectar" para usar uno existente o seleccionar uno nuevo.', 'system');
            } else {
                addSerialLine('ℹ️ Haz clic en "Conectar" para seleccionar un puerto serial.', 'system');
            }
        });
    }
}

function closeSerialMonitor() {
    document.getElementById('serialModal').classList.remove('active');
}

async function connectSerial() {
    const baudrate = parseInt(document.getElementById('serialBaudrate').value);
    
    // Verificar soporte de Web Serial API
    if (!('serial' in navigator)) {
        showToast('Web Serial API no está disponible en este navegador. Usa Chrome, Edge o Opera.', 'error');
        logToConsole('Web Serial API no disponible', 'error');
        return;
    }
    
    try {
        // Si ya hay un puerto seleccionado, intentar usarlo primero
        const existingPorts = await navigator.serial.getPorts();
        
        if (existingPorts.length > 0 && !serialPort) {
            // Usar el primer puerto disponible
            serialPort = existingPorts[0];
            addSerialLine(`Reutilizando puerto previamente seleccionado...`, 'system');
        } else if (!serialPort) {
            // Solicitar nuevo puerto al usuario
            serialPort = await navigator.serial.requestPort();
            addSerialLine(`Puerto seleccionado`, 'system');
        }
        
        // Si el puerto ya está abierto, cerrarlo primero
        if (serialPort.readable || serialPort.writable) {
            try {
                await serialPort.close();
            } catch (e) {
                // Ignorar errores al cerrar
            }
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
        updateSerialUI(true, 'Puerto Serial', baudrate);
        addSerialLine(`Conectado @ ${baudrate} baud`, 'system');
        updateConnectionStatus();
        
        // Iniciar lectura continua en segundo plano
        readSerialData().catch(error => {
            console.error('Error en lectura serial:', error);
        });
        
        showToast('Monitor serial conectado', 'success');
        logToConsole('Monitor serial conectado (Web Serial API)', 'success');
        
    } catch (error) {
        if (error.name === 'NotFoundError') {
            showToast('No se seleccionó ningún puerto', 'warning');
        } else if (error.name === 'SecurityError') {
            showToast('Error de seguridad. Verifica los permisos del navegador.', 'error');
        } else if (error.name === 'InvalidStateError') {
            showToast('El puerto ya está en uso. Desconecta primero.', 'warning');
        } else {
            showToast('Error al conectar: ' + error.message, 'error');
        }
        logToConsole('Error al conectar serial: ' + error.message, 'error');
        serialPort = null;
    }
}

async function disconnectSerial(silent = false) {
    try {
        if (!silent) {
            console.log('[SERIAL] Iniciando desconexión del monitor serial...');
        }
        
        // 1. Cancelar y liberar reader
        if (serialReader) {
            try {
                await serialReader.cancel();
            } catch (e) {
                console.warn('[SERIAL] Error cancelando reader:', e.message);
            }
            try {
                serialReader.releaseLock();
            } catch (e) {
                console.warn('[SERIAL] Error liberando lock del reader:', e.message);
            }
            serialReader = null;
        }
        
        // 2. Cerrar y liberar writer
        if (serialWriter) {
            try {
                serialWriter.releaseLock();
            } catch (e) {
                console.warn('[SERIAL] Error liberando lock del writer:', e.message);
            }
            serialWriter = null;
        }
        
        // 3. Cerrar puerto
        if (serialPort) {
            try {
                await serialPort.close();
            } catch (e) {
                console.warn('[SERIAL] Error cerrando puerto:', e.message);
            }
            serialPort = null;
        }
        
        // 4. Limpiar interval si existe
        if (serialReadInterval) {
            clearInterval(serialReadInterval);
            serialReadInterval = null;
        }
        
        // 5. Actualizar estado
        isSerialConnected = false;
        updateSerialUI(false);
        updateConnectionStatus();
        
        if (!silent) {
            addSerialLine('Desconectado', 'system');
            logToConsole('[SERIAL] Monitor serial desconectado correctamente', 'info');
        }
        
        // Pequeña espera para asegurar que el puerto se libere completamente
        await new Promise(r => setTimeout(r, 100));
        
        return true;
        
    } catch (error) {
        console.error('[SERIAL] Error crítico al desconectar:', error);
        // Forzar limpieza de estado aunque haya error
        serialReader = null;
        serialWriter = null;
        serialPort = null;
        isSerialConnected = false;
        updateSerialUI(false);
        return false;
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
                
                // Procesar líneas completas
                const lines = readBuffer.split('\n');
                readBuffer = lines.pop() || ''; // Mantener línea incompleta
                
                lines.forEach(line => {
                    if (line.trim()) {
                        addSerialLine(line.trim(), 'received');
                    }
                });
            }
        }
    } catch (error) {
        if (error.name !== 'NetworkError') {
            console.error('Error leyendo serial:', error);
            if (isSerialConnected) {
                await disconnectSerial();
                showToast('Error de lectura serial', 'error');
            }
        }
    }
}

async function sendSerialData() {
    if (!isSerialConnected || !serialWriter) return;
    
    const input = document.getElementById('serialInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    try {
        // Enviar mensaje con salto de línea
        await serialWriter.write(message + '\n');
        
        addSerialLine(`> ${message}`, 'sent');
        input.value = '';
        
    } catch (error) {
        console.error('Error enviando serial:', error);
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

function showBoardSuggestion(message, suggestedBoard) {
    /**
     * Muestra una sugerencia de cambio de placa con botón rápido.
     */
    const container = document.getElementById('toastContainer');
    
    // Remover sugerencias anteriores
    const existing = container.querySelector('.toast.suggestion');
    if (existing) existing.remove();
    
    const boardNames = {
        'arduino:avr:uno': 'Arduino UNO',
        'arduino:avr:nano': 'Arduino Nano',
        'arduino:avr:mega': 'Arduino Mega',
        'arduino:avr:leonardo': 'Arduino Leonardo'
    };
    
    const suggestedName = boardNames[suggestedBoard] || suggestedBoard;
    
    const toast = document.createElement('div');
    toast.className = 'toast warning suggestion';
    toast.innerHTML = `
        <span class="toast-icon">⚠️</span>
        <div style="flex: 1;">
            <span class="toast-message">${escapeHtml(message)}</span>
            <button class="btn btn-sm" style="margin-top: 8px; padding: 4px 12px; font-size: 12px;" 
                    onclick="changeBoardTo('${suggestedBoard}'); this.closest('.toast').remove();">
                Cambiar a ${suggestedName}
            </button>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    container.appendChild(toast);
    
    // No auto-remover, dejar que el usuario decida
}

function changeBoardTo(fqbn) {
    /**
     * Cambia la placa seleccionada al FQBN especificado.
     */
    const boardSelect = document.getElementById('boardSelect');
    const boardNames = {
        'arduino:avr:uno': 'Arduino UNO',
        'arduino:avr:nano': 'Arduino Nano',
        'arduino:avr:mega': 'Arduino Mega',
        'arduino:avr:leonardo': 'Arduino Leonardo'
    };
    
    if (boardSelect.querySelector(`option[value="${fqbn}"]`)) {
        boardSelect.value = fqbn;
        currentBoard = fqbn;
        const boardName = boardNames[fqbn] || fqbn;
        document.getElementById('boardInfo').innerHTML = `<span>🎯</span><span>${boardName}</span>`;
        logToConsole(`Placa cambiada a: ${boardName}`, 'success');
        showToast(`Placa cambiada a ${boardName}`, 'success');
    } else {
        logToConsole(`Placa ${fqbn} no disponible en el selector`, 'warning');
    }
}

// Exponer función globalmente para que funcione desde el onclick
window.changeBoardTo = changeBoardTo;

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// GESTIÓN DE PROYECTOS EN SERVIDOR
// ============================================

/**
 * Guarda el proyecto en el servidor
 */
async function saveProjectToServer() {
    if (!workspace) {
        showToast('No hay workspace disponible', 'error');
        return;
    }
    
    const xml = Blockly.Xml.workspaceToDom(workspace);
    const xmlText = Blockly.Xml.domToText(xml);
    const code = arduinoGenerator.workspaceToCode(workspace);
    
    // Si no hay proyecto actual, crear uno nuevo
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
    
    // Guardar el proyecto
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

/**
 * Abre el modal de proyectos
 */
async function openProjectsModal() {
    const modal = document.getElementById('projectsModal');
    if (!modal) return;
    
    modal.style.display = 'flex';
    await loadProjectsList();
}

/**
 * Carga la lista de proyectos
 */
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

/**
 * Carga un proyecto desde el servidor
 */
async function loadProjectFromServer(projectId) {
    try {
        const response = await fetch(`/api/projects/load/${projectId}/`);
        const data = await response.json();
        
        if (data.success && data.project) {
            currentProjectId = data.project.id;
            
            // Cargar XML en el workspace
            if (data.project.xml_content) {
                const xml = Blockly.utils.xml.textToDom(data.project.xml_content);
                workspace.clear();
                Blockly.Xml.domToWorkspace(xml, workspace);
                updateCode();
            }
            
            // Cerrar modal
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

/**
 * Crea un nuevo proyecto
 */
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
            
            // Cerrar modal de creación
            const createModal = document.getElementById('createProjectModal');
            if (createModal) createModal.style.display = 'none';
            
            // Limpiar formulario
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

/**
 * Obtiene el token CSRF
 */
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

// Función para cargar proyecto desde template (llamada desde index.html)
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
