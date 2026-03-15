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

    // Categorías Calvin - solo visibles en modo Calvin
    const TOOLBOX_CALVIN = `
        <category name="🤖 Calvin" colour="100" expanded="true">
            <category name="Calvin Control" colour="210">
                <block type="calvin_control_delay">
                    <value name="MS">
                        <block type="arduino_number"><field name="NUM">500</field></block>
                    </value>
                </block>
                <block type="calvin_control_if">
                    <value name="CONDITION"><block type="calvin_operator_compare"></block></value>
                </block>
                <block type="calvin_control_if_else">
                    <value name="CONDITION"><block type="calvin_operator_compare"></block></value>
                </block>
                <block type="calvin_control_switch">
                    <value name="VALUE"><block type="arduino_number"><field name="NUM">1</field></block></value>
                    <statement name="CASES">
                        <block type="calvin_control_case">
                            <value name="VALUE"><block type="arduino_number"><field name="NUM">1</field></block></value>
                        </block>
                        <block type="calvin_control_default"></block>
                    </statement>
                </block>
                <block type="calvin_control_case">
                    <value name="VALUE"><block type="arduino_number"><field name="NUM">0</field></block></value>
                </block>
                <block type="calvin_control_default"></block>
                <block type="calvin_control_while">
                    <value name="CONDITION"><block type="arduino_true"></block></value>
                </block>
                <block type="calvin_control_for">
                    <value name="FROM"><block type="arduino_number"><field name="NUM">0</field></block></value>
                    <value name="TO"><block type="arduino_number"><field name="NUM">10</field></block></value>
                    <value name="STEP"><block type="arduino_number"><field name="NUM">1</field></block></value>
                </block>
            </category>
            <category name="Calvin Operadores" colour="200">
                <block type="calvin_operator_number">
                    <field name="NUM">0</field>
                </block>
                <block type="calvin_operator_add">
                    <value name="A"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                    <value name="B"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                </block>
                <block type="calvin_operator_subtract">
                    <value name="A"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                    <value name="B"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                </block>
                <block type="calvin_operator_multiply">
                    <value name="A"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                    <value name="B"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                </block>
                <block type="calvin_operator_divide">
                    <value name="A"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                    <value name="B"><block type="calvin_operator_number"><field name="NUM">1</field></block></value>
                </block>
                <block type="calvin_operator_random">
                    <value name="MIN"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                    <value name="MAX"><block type="calvin_operator_number"><field name="NUM">100</field></block></value>
                </block>
                <block type="calvin_operator_gt">
                    <value name="A"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                    <value name="B"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                </block>
                <block type="calvin_operator_lt">
                    <value name="A"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                    <value name="B"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                </block>
                <block type="calvin_operator_eq">
                    <value name="A"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                    <value name="B"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                </block>
                <block type="calvin_operator_and">
                    <value name="A"><block type="arduino_true"></block></value>
                    <value name="B"><block type="arduino_false"></block></value>
                </block>
                <block type="calvin_operator_or">
                    <value name="A"><block type="arduino_true"></block></value>
                    <value name="B"><block type="arduino_false"></block></value>
                </block>
                <block type="calvin_operator_sqrt">
                    <value name="X"><block type="calvin_operator_number"><field name="NUM">16</field></block></value>
                </block>
                <block type="calvin_operator_compare">
                    <value name="A"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                    <value name="B"><block type="calvin_operator_number"><field name="NUM">0</field></block></value>
                </block>
            </category>
            <category name="Calvin Texto" colour="160">
                <block type="calvin_text_string">
                    <field name="TEXT">texto</field>
                </block>
                <block type="calvin_text_concat">
                    <value name="A"><block type="calvin_text_string"><field name="TEXT">Hola</field></block></value>
                    <value name="B"><block type="calvin_text_string"><field name="TEXT">mundo</field></block></value>
                </block>
            </category>
            <category name="Calvin Serial" colour="20">
                <block type="calvin_serial_begin"></block>
                <block type="calvin_serial_set_timeout">
                    <value name="MS"><block type="calvin_operator_number"><field name="NUM">1000</field></block></value>
                </block>
                <block type="calvin_serial_print">
                    <value name="VALUE"><block type="calvin_text_string"><field name="TEXT">Hola</field></block></value>
                </block>
                <block type="calvin_serial_has_data"></block>
                <block type="calvin_serial_read_string"></block>
            </category>
            <category name="Calvin BLE (ESP32)" colour="280">
                <block type="calvin_ble_init">
                    <field name="NAME">CalvinBot</field>
                    <statement name="SERVICES">
                        <block type="calvin_ble_service">
                            <field name="UUID">4fafc201-1fb5-459e-8fcc-c5c9c331914b</field>
                            <statement name="CHARACTERISTICS">
                                <block type="calvin_ble_characteristic">
                                    <field name="UUID">beb5483e-36e1-4688-b7f5-ea07361b26a8</field>
                                    <field name="NAME">cmd</field>
                                </block>
                            </statement>
                        </block>
                    </statement>
                </block>
                <block type="calvin_ble_service">
                    <field name="UUID">4fafc201-1fb5-459e-8fcc-c5c9c331914b</field>
                </block>
                <block type="calvin_ble_characteristic">
                    <field name="UUID">beb5483e-36e1-4688-b7f5-ea07361b26a8</field>
                    <field name="NAME">cmd</field>
                </block>
                <block type="calvin_ble_write">
                    <field name="CHAR">cmd</field>
                    <value name="VALUE"><block type="calvin_text_string"><field name="TEXT">Hola</field></block></value>
                </block>
                <block type="calvin_ble_char_value_number"></block>
                <block type="calvin_ble_char_value_string"></block>
            </category>
            <category name="Calvin I/O" colour="230">
                <block type="calvin_io_high_low">
                    <field name="VAL">HIGH</field>
                </block>
                <block type="calvin_io_digital_write">
                    <field name="PIN">13</field>
                    <value name="STAT">
                        <block type="calvin_io_high_low">
                            <field name="VAL">HIGH</field>
                        </block>
                    </value>
                </block>
                <block type="calvin_io_digital_read">
                    <field name="PIN">2</field>
                </block>
                <block type="calvin_io_analog_read">
                    <field name="PIN">0</field>
                </block>
                <block type="calvin_io_analog_write">
                    <field name="PIN">9</field>
                    <value name="VALUE">
                        <block type="calvin_operator_number"><field name="NUM">128</field></block>
                    </value>
                </block>
            </category>
            <category name="Calvin Funciones" colour="290">
                <block type="calvin_func_defnoreturn">
                    <field name="NAME">miFuncion</field>
                </block>
                <block type="calvin_func_defreturn">
                    <field name="NAME">calcular</field>
                    <field name="RETURN_TYPE">int</field>
                    <value name="RETURN"><block type="arduino_number"><field name="NUM">0</field></block></value>
                </block>
                <block type="calvin_func_ifreturn">
                    <value name="CONDITION"><block type="arduino_true"></block></value>
                    <value name="VALUE"><block type="arduino_number"><field name="NUM">0</field></block></value>
                </block>
                <block type="calvin_func_call">
                    <field name="NAME">miFuncion</field>
                </block>
                <block type="calvin_func_call_return">
                    <field name="NAME">calcular</field>
                </block>
            </category>
            <category name="Calvin Variables" colour="290">
                <label text="── Crear variable de texto ──"></label>
                <block type="arduino_variable_string">
                    <field name="NAME">texto</field>
                    <value name="VALUE"><block type="arduino_string"><field name="TEXT"></field></block></value>
                </block>
                <label text="── Crear variable numérica ──"></label>
                <block type="arduino_variable_int">
                    <field name="NAME">numero</field>
                    <value name="VALUE"><block type="arduino_number"><field name="NUM">0</field></block></value>
                </block>
                <block type="arduino_variable_float">
                    <field name="NAME">decimal</field>
                    <value name="VALUE"><block type="arduino_number"><field name="NUM">0</field></block></value>
                </block>
                <label text="── Crear variable de color ──"></label>
                <block type="arduino_variable_string">
                    <field name="NAME">color</field>
                    <value name="VALUE"><block type="arduino_string"><field name="TEXT">#000000</field></block></value>
                </block>
                <label text="── Usar variables ──"></label>
                <block type="arduino_get_variable">
                    <field name="NAME">variable</field>
                </block>
                <block type="calvin_var_set">
                    <value name="VALUE"><block type="arduino_number"><field name="NUM">0</field></block></value>
                </block>
            </category>
            <category name="Calvin BotFlow Nivel 1" colour="100">
                <block type="calvin_botflow1_step"></block>
                <block type="calvin_botflow1_init_proximidad">
                    <field name="TRIG">6</field>
                    <field name="ECHO">7</field>
                </block>
                <block type="calvin_botflow1_distancia"></block>
                <block type="calvin_botflow1_init_nota">
                    <field name="PIN">3</field>
                </block>
                <block type="calvin_botflow1_nota_octava">
                    <field name="NOTA">DO</field>
                    <field name="OCTAVA">4</field>
                    <value name="DURACION"><block type="calvin_operator_number"><field name="NUM">1</field></block></value>
                </block>
                <block type="calvin_botflow1_init_rgb">
                    <field name="TIPO">A</field>
                    <field name="R">5</field>
                    <field name="G">6</field>
                    <field name="B">11</field>
                </block>
                <block type="calvin_botflow1_led_color">
                    <field name="COLOR">rojo</field>
                    <value name="DURACION"><block type="calvin_operator_number"><field name="NUM">1</field></block></value>
                </block>
                <block type="calvin_botflow1_init_motores">
                    <field name="PWM">30</field>
                    <field name="IZQ">9</field>
                    <field name="DER">10</field>
                </block>
                <block type="calvin_botflow1_adelante">
                    <value name="SEG"><block type="calvin_operator_number"><field name="NUM">1</field></block></value>
                </block>
                <block type="calvin_botflow1_girar_motor">
                    <field name="LADO">0</field>
                    <field name="SENTIDO">0</field>
                    <value name="SEG"><block type="calvin_operator_number"><field name="NUM">1</field></block></value>
                </block>
            </category>
            <category name="Calvin BotFlow Nivel 2" colour="120">
                <block type="calvin_botflow2_condition">
                    <value name="COND"><block type="arduino_true"></block></value>
                </block>
                <block type="calvin_botflow2_init_lineas">
                    <field name="IZQ">0</field>
                    <field name="CENT">1</field>
                    <field name="DER">2</field>
                </block>
                <block type="calvin_botflow2_calibrar_lineas">
                    <value name="N"><block type="calvin_operator_number"><field name="NUM">50</field></block></value>
                </block>
                <block type="calvin_botflow2_linea_valor">
                    <field name="LADO">1</field>
                </block>
                <block type="calvin_botflow2_linea_umbral">
                    <field name="LADO">1</field>
                </block>
            </category>
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
     * @returns {string} XML del toolbox
     */
    function getToolboxXml(robot) {
        const robotCat = (robot === 'Calvin') ? TOOLBOX_CALVIN : TOOLBOX_MAX;
        return '<xml>' + TOOLBOX_BASE + robotCat + TOOLBOX_AVANZADO + '</xml>';
    }

    /**
     * Construye el toolbox en el elemento DOM
     * @param {string} robot - 'MAX' o 'Calvin'
     * @param {HTMLElement} el - elemento con id="toolbox"
     */
    function buildToolboxElement(robot, el) {
        if (!el) return;
        el.innerHTML = getToolboxXml(robot);
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
