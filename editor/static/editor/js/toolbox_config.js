/**
 * MAX-IDE - Toolbox final por robot (MAX / Calvin)
 * - Modo MAX: bloques base + Carrito MAX | oculta Calvin
 * - Modo Calvin: bloques base + Calvin (Control, Operadores, ...) | oculta Carrito MAX
 * - Persistencia: localStorage key maxide_robot
 * - Al cambiar: solo toolbox se actualiza; workspace se preserva
 */
(function() {
    'use strict';

    const ROBOT_KEY = 'maxide_robot';

    // Categorías base Arduino (comunes a todos los robots)
    const TOOLBOX_BASE = `
        <category name="⚙️ Estructura" colour="60">
            <block type="arduino_setup"></block>
            <block type="arduino_loop"></block>
        </category>
        
        <category name="📌 Digital" colour="230">
            <block type="arduino_pin_mode">
                <field name="PIN">13</field>
                <field name="MODE">OUTPUT</field>
            </block>
            <block type="arduino_digital_write">
                <field name="PIN">13</field>
                <field name="VALUE">HIGH</field>
            </block>
            <block type="arduino_digital_read">
                <field name="PIN">2</field>
            </block>
        </category>
        
        <category name="📊 Analógico" colour="180">
            <block type="arduino_analog_read">
                <field name="PIN">0</field>
            </block>
            <block type="arduino_analog_write">
                <field name="PIN">9</field>
                <value name="VALUE">
                    <block type="arduino_number">
                        <field name="NUM">128</field>
                    </block>
                </value>
            </block>
        </category>
        
        <category name="⏱️ Tiempo" colour="330">
            <block type="arduino_delay">
                <value name="TIME">
                    <block type="arduino_number">
                        <field name="NUM">1000</field>
                    </block>
                </value>
            </block>
            <block type="arduino_delay_microseconds">
                <value name="TIME">
                    <block type="arduino_number">
                        <field name="NUM">100</field>
                    </block>
                </value>
            </block>
            <block type="arduino_millis"></block>
            <block type="arduino_micros"></block>
        </category>
        
        <category name="📡 Serial" colour="20">
            <block type="arduino_serial_begin">
                <field name="BAUD">9600</field>
            </block>
            <block type="arduino_serial_print"></block>
            <block type="arduino_serial_println"></block>
            <block type="arduino_serial_available"></block>
            <block type="arduino_serial_read"></block>
        </category>
        
        <category name="🔀 Control" colour="210">
            <label text="── Condicionales ──"></label>
            <block type="arduino_if"></block>
            <block type="arduino_if_else"></block>
            <block type="arduino_if_elseif"></block>
            <block type="arduino_if_elseif_else"></block>
            <block type="arduino_if_elseif2_else"></block>
            <label text="── Ciclos ──"></label>
            <block type="arduino_for">
                <field name="VAR">i</field>
                <field name="FROM">0</field>
                <field name="TO">10</field>
            </block>
            <block type="arduino_while"></block>
        </category>
        
        <category name="⚖️ Lógica" colour="210">
            <block type="arduino_compare"></block>
            <block type="arduino_and"></block>
            <block type="arduino_or"></block>
            <block type="arduino_and3"></block>
            <block type="arduino_or3"></block>
            <block type="arduino_and_or"></block>
            <block type="arduino_or_and"></block>
            <block type="arduino_logic"></block>
            <block type="arduino_not"></block>
            <block type="arduino_true"></block>
            <block type="arduino_false"></block>
        </category>
        
        <category name="🔢 Matemáticas" colour="200">
            <block type="arduino_number">
                <field name="NUM">0</field>
            </block>
            <block type="arduino_math"></block>
            <block type="arduino_map"></block>
            <block type="arduino_constrain"></block>
            <block type="arduino_random"></block>
        </category>
        
        <category name="📝 Variables" colour="290">
            <block type="arduino_variable_int"></block>
            <block type="arduino_variable_float"></block>
            <block type="arduino_variable_string"></block>
            <block type="arduino_variable_boolean"></block>
            <block type="arduino_get_variable"></block>
            <block type="arduino_set_variable"></block>
        </category>
        
        <category name="📝 Texto" colour="160">
            <block type="arduino_string">
                <field name="TEXT">Hola</field>
            </block>
        </category>
        
        <category name="🔧 Componentes" colour="40">
            <block type="arduino_led_builtin">
                <field name="STATE">HIGH</field>
            </block>
            <block type="arduino_tone"></block>
            <block type="arduino_no_tone"></block>
        </category>
        
        <category name="🦾 Servos" colour="270">
            <block type="arduino_servo_attach">
                <field name="NAME">miServo</field>
                <field name="PIN">9</field>
            </block>
            <block type="arduino_servo_attach_limits">
                <field name="NAME">miServo</field>
                <field name="PIN">9</field>
                <field name="MIN">544</field>
                <field name="MAX">2400</field>
            </block>
            <block type="arduino_servo_write">
                <field name="NAME">miServo</field>
                <value name="ANGLE">
                    <block type="arduino_number">
                        <field name="NUM">90</field>
                    </block>
                </value>
            </block>
            <block type="arduino_servo_write_simple">
                <field name="NAME">miServo</field>
                <field name="ANGLE">90</field>
            </block>
            <block type="arduino_servo_write_microseconds">
                <field name="NAME">miServo</field>
                <value name="US">
                    <block type="arduino_number">
                        <field name="NUM">1500</field>
                    </block>
                </value>
            </block>
            <block type="arduino_servo_read">
                <field name="NAME">miServo</field>
            </block>
            <block type="arduino_servo_attached">
                <field name="NAME">miServo</field>
            </block>
            <block type="arduino_servo_detach">
                <field name="NAME">miServo</field>
            </block>
            <block type="arduino_servo_sweep">
                <field name="NAME">miServo</field>
                <field name="FROM">0</field>
                <field name="TO">180</field>
                <value name="DELAY">
                    <block type="arduino_number">
                        <field name="NUM">15</field>
                    </block>
                </value>
            </block>
        </category>`;

    // Categoría Carrito MAX
    const TOOLBOX_MAX = `
        <category name="🚗 Carrito MAX" colour="190" expanded="false">
            <category name="⚙️ Inicialización" colour="190">
                <block type="max_init_motores">
                    <field name="PIN_IZQ">9</field>
                    <field name="PIN_DER">10</field>
                </block>
                <block type="max_init_distancia">
                    <field name="PIN_TRIG">6</field>
                    <field name="PIN_ECHO">7</field>
                </block>
                <block type="max_init_lineas">
                    <field name="PIN_IZQ">0</field>
                    <field name="PIN_CENT">1</field>
                    <field name="PIN_DER">2</field>
                </block>
                <block type="max_init_buzzer">
                    <field name="PIN">3</field>
                </block>
                <block type="max_init_garra">
                    <field name="PIN">11</field>
                    <field name="CERRADA">0</field>
                    <field name="ABIERTA">90</field>
                </block>
            </category>
            <category name="🏎️ Movimiento" colour="120">
                <block type="max_adelante">
                    <field name="VEL">30</field>
                </block>
                <block type="max_atras">
                    <field name="VEL">30</field>
                </block>
                <block type="max_izquierda">
                    <field name="VEL">25</field>
                </block>
                <block type="max_derecha">
                    <field name="VEL">25</field>
                </block>
                <block type="max_detener"></block>
                <block type="max_adelante_var"></block>
                <block type="max_atras_var"></block>
                <block type="max_izquierda_var"></block>
                <block type="max_derecha_var"></block>
                <block type="max_avanzar_tiempo">
                    <field name="VEL">30</field>
                    <field name="TIEMPO">1000</field>
                </block>
                <block type="max_retroceder_tiempo">
                    <field name="VEL">30</field>
                    <field name="TIEMPO">1000</field>
                </block>
                <block type="max_girar_tiempo">
                    <field name="DIR">izquierda</field>
                    <field name="VEL">25</field>
                    <field name="TIEMPO">500</field>
                </block>
            </category>
            <category name="📡 Sensor Distancia" colour="230">
                <block type="max_medir_distancia"></block>
                <block type="max_distancia_menor_que">
                    <field name="CM">20</field>
                </block>
                <block type="max_distancia_mayor_que">
                    <field name="CM">30</field>
                </block>
                <block type="max_evitar_obstaculo">
                    <field name="DISTANCIA">20</field>
                </block>
            </category>
            <category name="➖ Sensor Líneas" colour="60">
                <block type="max_leer_linea_izq"></block>
                <block type="max_leer_linea_centro"></block>
                <block type="max_leer_linea_der"></block>
                <block type="max_linea_detectada">
                    <field name="SENSOR">CENT</field>
                    <field name="UMBRAL">500</field>
                </block>
                <block type="max_linea_comparar">
                    <field name="SENSOR">CENT</field>
                    <field name="OP"><</field>
                    <field name="UMBRAL">500</field>
                </block>
                <block type="max_linea_valor_comparar">
                    <field name="SENSOR">CENT</field>
                    <field name="OP"><</field>
                </block>
            </category>
            <category name="🎵 Buzzer/Sonido" colour="300">
                <block type="max_tocar_nota">
                    <field name="NOTA">262</field>
                    <field name="DURACION">300</field>
                </block>
                <block type="max_tocar_frecuencia">
                    <value name="FREQ">
                        <block type="arduino_number">
                            <field name="NUM">440</field>
                        </block>
                    </value>
                    <value name="DURACION">
                        <block type="arduino_number">
                            <field name="NUM">300</field>
                        </block>
                    </value>
                </block>
                <block type="max_beep"></block>
                <block type="max_detener_sonido"></block>
            </category>
            <category name="🦾 Garra" colour="45">
                <block type="max_abrir_garra"></block>
                <block type="max_cerrar_garra"></block>
                <block type="max_mover_garra">
                    <field name="ANGULO">45</field>
                </block>
            </category>
        </category>`;

    // Base mínima para Calvin: solo Estructura (setup/loop). Calvin ya aporta Control, Serial,
    // Operadores/Matemáticas/Lógica, Variables, Texto, I/O (Digital/Analógico), Componentes (BotFlow).
    const TOOLBOX_BASE_CALVIN = `
        <category name="⚙️ Estructura" colour="60">
            <block type="arduino_setup"></block>
            <block type="arduino_loop"></block>
        </category>
        `;

    // Categorías Calvin - solo visibles en modo Calvin
    const TOOLBOX_CALVIN = `
            <category name="Calvin Control" colour="210">
                <block type="base_delay">
                    <value name="DELAY_TIME">
                        <shadow type="arduino_number"><field name="NUM">500</field></shadow>
                    </value>
                </block>
                <block type="controls_if"></block>
                <block type="controls_ifelse"></block>
                <block type="logic_compare">
                    <field name="OP">EQ</field>
                    <value name="A"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                    <value name="B"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                </block>
                <block type="logic_negate"></block>
                <block type="logic_operation">
                    <field name="OP">AND</field>
                </block>
                <block type="switch_case">
                    <value name="VARIABLE"><block type="arduino_number"><field name="NUM">1</field></block></value>
                </block>
                <block type="case">
                    <value name="VALUE"><block type="arduino_number"><field name="NUM">0</field></block></value>
                </block>
                <block type="controls_whileUntil">
                    <field name="MODE">WHILE</field>
                </block>
                <block type="controls_for">
                    <value name="FROM"><block type="arduino_number"><field name="NUM">0</field></block></value>
                    <value name="TO"><block type="arduino_number"><field name="NUM">10</field></block></value>
                    <value name="BY"><block type="arduino_number"><field name="NUM">1</field></block></value>
                </block>
            </category>
            <category name="Calvin Operadores" colour="200">
                <block type="math_number">
                    <field name="NUM">0</field>
                </block>
                <block type="sumar">
                    <value name="A"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                    <value name="B"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                </block>
                <block type="restar">
                    <value name="A"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                    <value name="B"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                </block>
                <block type="multiplicar">
                    <value name="A"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                    <value name="B"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                </block>
                <block type="dividir">
                    <value name="A"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                    <value name="B"><shadow type="math_number"><field name="NUM">1</field></shadow></value>
                </block>
                <block type="math_random_int">
                    <value name="FROM"><shadow type="math_number"><field name="NUM">1</field></shadow></value>
                    <value name="TO"><shadow type="math_number"><field name="NUM">10</field></shadow></value>
                </block>
                <block type="mayor_que">
                    <value name="A"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                    <value name="B"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                </block>
                <block type="menor_que">
                    <value name="A"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                    <value name="B"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                </block>
                <block type="igual_que">
                    <value name="A"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                    <value name="B"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                </block>
                <block type="logica_y"></block>
                <block type="logica_o"></block>
                <block type="math_single">
                    <field name="OP">ROOT</field>
                    <value name="NUM"><shadow type="math_number"><field name="NUM">9</field></shadow></value>
                </block>
            </category>
            <category name="Calvin Texto" colour="160">
                <block type="text">
                    <field name="TEXT"></field>
                </block>
            </category>
            <category name="Calvin Serial" colour="20">
                <block type="serial_init">
                    <value name="BADURATE">
                        <shadow type="math_number"><field name="NUM">115200</field></shadow>
                    </value>
                </block>
                <block type="serial_timeout">
                    <value name="TIMEOUT">
                        <shadow type="math_number"><field name="NUM">10</field></shadow>
                    </value>
                </block>
                <block type="serial_print">
                    <value name="CONTENT">
                        <shadow type="text"><field name="TEXT"></field></shadow>
                    </value>
                </block>
                <block type="serial_disponible"></block>
                <block type="serial_read"></block>
            </category>
            <category name="Calvin BLE (ESP32)" colour="280">
                <block type="calvin_ble_init">
                    <value name="NOMBRE"><block type="calvin_text_string"><field name="TEXT">CalvinBot</field></block></value>
                    <statement name="SERVICES">
                        <block type="calvin_ble_service">
                            <field name="NOMBRE">servicio</field>
                            <field name="UUID">4fafc201-1fb5-459e-8fcc-c5c9c331914b</field>
                            <statement name="CHARACTERISTICS">
                                <block type="calvin_ble_characteristic">
                                    <field name="NOMBRE">cmd</field>
                                    <field name="UUID">beb5483e-36e1-4688-b7f5-ea07361b26a8</field>
                                </block>
                            </statement>
                        </block>
                    </statement>
                </block>
                <block type="calvin_ble_service">
                    <field name="NOMBRE">servicio</field>
                    <field name="UUID">4fafc201-1fb5-459e-8fcc-c5c9c331914b</field>
                </block>
                <block type="calvin_ble_characteristic">
                    <field name="NOMBRE">cmd</field>
                    <field name="UUID">beb5483e-36e1-4688-b7f5-ea07361b26a8</field>
                </block>
                <block type="calvin_ble_write">
                    <field name="SERVICIO">servicio</field>
                    <field name="CARACTERISTICA">cmd</field>
                    <value name="VALUE"><block type="calvin_text_string"><field name="TEXT">Hola</field></block></value>
                </block>
                <block type="calvin_ble_char_value_number"></block>
                <block type="calvin_ble_char_value_string"></block>
            </category>
            <category name="Calvin I/O" colour="230">
                <block type="inout_highlow">
                    <field name="BOOL">HIGH</field>
                </block>
                <block type="inout_digital_write">
                    <field name="PIN">13</field>
                    <field name="STAT">HIGH</field>
                </block>
                <block type="inout_digital_read">
                    <field name="PIN">2</field>
                </block>
                <block type="inout_analog_read">
                    <field name="PIN">A0</field>
                </block>
                <block type="inout_analog_write">
                    <field name="PIN">9</field>
                    <value name="NUM"><shadow type="math_number"><field name="NUM">128</field></shadow></value>
                </block>
            </category>
            <category name="Calvin Funciones" colour="290" custom="CALVIN_FUNCTIONS_FLYOUT"></category>
            <category name="Calvin Variables" colour="290" custom="CALVIN_VARIABLES_FLYOUT"></category>
            <category name="Calvin BotFlow Nivel 1" colour="100">
                <block type="calvin_botflow1_init_proximidad"></block>
                <block type="calvin_botflow1_distancia"></block>
                <block type="calvin_botflow1_init_nota"></block>
                <block type="calvin_botflow1_nota_octava">
                    <field name="nota">NOTE_C</field>
                    <field name="octava">0</field>
                    <field name="durnota">inf</field>
                </block>
                <block type="calvin_botflow1_init_rgb">
                    <field name="tipoLED">A</field>
                </block>
                <block type="calvin_botflow1_led_color">
                    <field name="estado">true</field>
                    <field name="color">rojo</field>
                    <field name="durled">inf</field>
                </block>
                <block type="calvin_botflow1_init_motores">
                    <field name="pwmvalue">220</field>
                </block>
                <block type="calvin_botflow1_mover">
                    <field name="movimiento">1</field>
                    <value name="TIEMPO"><block type="calvin_operator_number"><field name="NUM">1</field></block></value>
                </block>
                <block type="calvin_botflow1_girar_motor">
                    <field name="motor">0</field>
                    <field name="sentido">1</field>
                    <value name="TIEMPO"><block type="calvin_operator_number"><field name="NUM">1</field></block></value>
                </block>
            </category>
            <category name="Calvin BotFlow Nivel 2" colour="120">
                <block type="calvin_botflow2_init_lineas"></block>
                <block type="calvin_botflow2_calibrar_lineas">
                    <field name="ciclos">30</field>
                </block>
                <block type="calvin_botflow2_linea_valor">
                    <field name="sensor">s_izquierdo</field>
                </block>
                <block type="calvin_botflow2_linea_umbral">
                    <field name="umbralSensor">s_izquierdo</field>
                </block>
            </category>`;

    // Avanzado (siempre al final)
    const TOOLBOX_AVANZADO = `
        <category name="⚡ Avanzado" colour="0">
            <block type="arduino_include">
                <field name="LIBRARY">Servo.h</field>
            </block>
            <block type="arduino_custom_code"></block>
            <block type="arduino_comment"></block>
        </category>`;

    /**
     * Obtiene el robot almacenado (MAX o Calvin)
     */
    function getStoredRobot() {
        try {
            const r = localStorage.getItem(ROBOT_KEY);
            return (r === 'Calvin' || r === 'MAX') ? r : 'MAX';
        } catch (e) {
            return 'MAX';
        }
    }

    /**
     * Guarda la selección del robot
     */
    function setStoredRobot(robot) {
        try {
            localStorage.setItem(ROBOT_KEY, robot);
        } catch (e) { /* ignore */ }
    }

    /**
     * Devuelve el XML completo del toolbox según el robot
     * @param {string} robot - 'MAX' o 'Calvin'
     * @returns {string} XML del toolbox (contenido para hijos directos de #toolbox)
     */
    function getToolboxXml(robot) {
        const robotCat = (robot === 'Calvin') ? TOOLBOX_CALVIN : TOOLBOX_MAX;
        const base = (robot === 'Calvin') ? TOOLBOX_BASE_CALVIN : TOOLBOX_BASE;
        return base + robotCat + TOOLBOX_AVANZADO;
    }

    /**
     * Construye el toolbox en el elemento DOM.
     * El elemento #toolbox es <xml>: sus hijos deben ser <category> directamente.
     * Evitar <xml> anidado que Blockly no interpreta correctamente.
     * @param {string} robot - 'MAX' o 'Calvin'
     * @param {HTMLElement} el - elemento con id="toolbox"
     */
    function buildToolboxElement(robot, el) {
        if (!el) return;
        el.innerHTML = getToolboxXml(robot).trim();
    }

    /**
     * Detecta si el workspace tiene bloques del otro robot (max_* al cambiar a Calvin, calvin_* al cambiar a MAX)
     * @param {Blockly.Workspace} ws - workspace de Blockly
     * @param {string} targetRobot - 'MAX' o 'Calvin'
     * @returns {boolean}
     */
    function hasCrossRobotBlocks(ws, targetRobot) {
        if (!ws || !targetRobot) return false;
        const blocks = ws.getAllBlocks(false);
        const otherPrefix = targetRobot === 'Calvin' ? 'max_' : 'calvin_';
        return blocks.some(function(b) { return b.type && b.type.indexOf(otherPrefix) === 0; });
    }

    window.ToolboxConfig = {
        ROBOT_KEY: ROBOT_KEY,
        getStoredRobot: getStoredRobot,
        setStoredRobot: setStoredRobot,
        getToolboxXml: getToolboxXml,
        buildToolboxElement: buildToolboxElement,
        hasCrossRobotBlocks: hasCrossRobotBlocks,
        ROBOTS: ['MAX', 'Calvin']
    };
})();
