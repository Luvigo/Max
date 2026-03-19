/**
 * Bloques Calvin - Familia técnica separada
 * Naming: calvin_control_*, calvin_operator_*, calvin_text_*, etc.
 * Extensión de MAX-IDE; no modifica max_* ni arduino_*
 */

(function() {
    'use strict';

    if (typeof Blockly === 'undefined') return;

    const COLOUR_CONTROL = 210;
    const COLOUR_OPERATOR = 200;
    const COLOUR_TEXT = 160;
    const COLOUR_SERIAL = 20;
    const COLOUR_BLE = 280;
    const COLOUR_IO = 230;
    const COLOUR_FUNC = 290;
    const COLOUR_VAR = 290;
    const COLOUR_BOTFLOW1 = 100;
    const COLOUR_BOTFLOW2 = 120;

    // ============================================
    // calvin_control_* - Control de flujo
    // ============================================

    // 1) Esperar [n] ms
    Blockly.Blocks['calvin_control_delay'] = {
        init: function() {
            this.appendValueInput("MS").setCheck("Number").appendField("Esperar");
            this.appendDummyInput().appendField("ms");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_CONTROL);
            this.setTooltip("Espera un tiempo en milisegundos");
        }
    };

    // 2) En caso de que [valor] ... (contiene Sea y Si nada se cumplió)
    Blockly.Blocks['calvin_control_switch'] = {
        init: function() {
            this.appendValueInput("VALUE").setCheck(null).appendField("En caso de que");
            this.appendStatementInput("CASES").setCheck(null).appendField("hacer");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_CONTROL);
            this.setTooltip("Switch/case - Añade bloques Sea y Si nada se cumplió dentro");
        }
    };

    // 3) Sea [valor] Hacer ... (caso del switch)
    Blockly.Blocks['calvin_control_case'] = {
        init: function() {
            this.appendDummyInput().appendField("Sea");
            this.appendValueInput("VALUE").setCheck(null).appendField("");
            this.appendDummyInput().appendField("Hacer");
            this.appendStatementInput("DO").setCheck(null).appendField("");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_CONTROL);
            this.setTooltip("Caso del switch");
        }
    };

    // 4) Si nada se cumplió (default del switch)
    Blockly.Blocks['calvin_control_default'] = {
        init: function() {
            this.appendDummyInput().appendField("Si nada se cumplió");
            this.appendStatementInput("DO").setCheck(null).appendField("hacer");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_CONTROL);
            this.setTooltip("Bloque por defecto cuando no coincide ningún caso");
        }
    };

    // 5) repetir mientras [condición] hacer ...
    Blockly.Blocks['calvin_control_while'] = {
        init: function() {
            this.appendValueInput("CONDITION")
                .setCheck("Boolean")
                .appendField("repetir mientras");
            this.appendStatementInput("DO")
                .setCheck(null)
                .appendField("hacer");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_CONTROL);
            this.setTooltip("Repite mientras la condición sea verdadera");
        }
    };

    // 6) contar [i] de [inicio] a [fin] añadiendo [paso] hacer ...
    Blockly.Blocks['calvin_control_for'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("contar")
                .appendField(new Blockly.FieldTextInput("i"), "VAR")
                .appendField("de");
            this.appendValueInput("FROM").setCheck("Number").appendField("");
            this.appendDummyInput().appendField("a");
            this.appendValueInput("TO").setCheck("Number").appendField("");
            this.appendDummyInput().appendField("añadiendo");
            this.appendValueInput("STEP").setCheck("Number").appendField("");
            this.appendStatementInput("DO").setCheck(null).appendField("hacer");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_CONTROL);
            this.setTooltip("Bucle for con variable, inicio, fin y paso");
        }
    };

    // 7) si [condición] entonces ...
    Blockly.Blocks['calvin_control_if'] = {
        init: function() {
            this.appendValueInput("CONDITION")
                .setCheck("Boolean")
                .appendField("si");
            this.appendStatementInput("DO")
                .setCheck(null)
                .appendField("entonces");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_CONTROL);
            this.setTooltip("Ejecuta código si la condición es verdadera");
        }
    };

    // 8) si [condición] entonces ... si no ...
    Blockly.Blocks['calvin_control_if_else'] = {
        init: function() {
            this.appendValueInput("CONDITION")
                .setCheck("Boolean")
                .appendField("si");
            this.appendStatementInput("DO")
                .setCheck(null)
                .appendField("entonces");
            this.appendStatementInput("ELSE")
                .setCheck(null)
                .appendField("si no");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_CONTROL);
            this.setTooltip("Si la condición es verdadera hace una cosa, si no hace otra");
        }
    };

    // ============================================
    // calvin_operator_* - Operadores
    // ============================================

    // número literal
    Blockly.Blocks['calvin_operator_number'] = {
        init: function() {
            this.appendDummyInput()
                .appendField(new Blockly.FieldNumber(0), "NUM");
            this.setOutput(true, "Number");
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip("Un número");
        }
    };

    // suma
    Blockly.Blocks['calvin_operator_add'] = {
        init: function() {
            this.appendValueInput("A").setCheck("Number").appendField("suma");
            this.appendValueInput("B").setCheck("Number").appendField("y");
            this.setInputsInline(true);
            this.setOutput(true, "Number");
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip("Suma dos números");
        }
    };

    // resta
    Blockly.Blocks['calvin_operator_subtract'] = {
        init: function() {
            this.appendValueInput("A").setCheck("Number").appendField("resta");
            this.appendValueInput("B").setCheck("Number").appendField("menos");
            this.setInputsInline(true);
            this.setOutput(true, "Number");
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip("Resta dos números");
        }
    };

    // multiplicación
    Blockly.Blocks['calvin_operator_multiply'] = {
        init: function() {
            this.appendValueInput("A").setCheck("Number").appendField("multiplicación");
            this.appendValueInput("B").setCheck("Number").appendField("por");
            this.setInputsInline(true);
            this.setOutput(true, "Number");
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip("Multiplica dos números");
        }
    };

    // división
    Blockly.Blocks['calvin_operator_divide'] = {
        init: function() {
            this.appendValueInput("A").setCheck("Number").appendField("división");
            this.appendValueInput("B").setCheck("Number").appendField("entre");
            this.setInputsInline(true);
            this.setOutput(true, "Number");
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip("Divide dos números");
        }
    };

    // número aleatorio entre X y Y
    Blockly.Blocks['calvin_operator_random'] = {
        init: function() {
            this.appendValueInput("MIN").setCheck("Number").appendField("número aleatorio entre");
            this.appendValueInput("MAX").setCheck("Number").appendField("y");
            this.setInputsInline(true);
            this.setOutput(true, "Number");
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip("Genera un número aleatorio en el rango");
        }
    };

    // > (mayor que)
    Blockly.Blocks['calvin_operator_gt'] = {
        init: function() {
            this.appendValueInput("A").setCheck(null).appendField("");
            this.appendDummyInput().appendField(">");
            this.appendValueInput("B").setCheck(null).appendField("");
            this.setInputsInline(true);
            this.setOutput(true, "Boolean");
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip("Mayor que");
        }
    };

    // < (menor que)
    Blockly.Blocks['calvin_operator_lt'] = {
        init: function() {
            this.appendValueInput("A").setCheck(null).appendField("");
            this.appendDummyInput().appendField("<");
            this.appendValueInput("B").setCheck(null).appendField("");
            this.setInputsInline(true);
            this.setOutput(true, "Boolean");
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip("Menor que");
        }
    };

    // = (igual)
    Blockly.Blocks['calvin_operator_eq'] = {
        init: function() {
            this.appendValueInput("A").setCheck(null).appendField("");
            this.appendDummyInput().appendField("=");
            this.appendValueInput("B").setCheck(null).appendField("");
            this.setInputsInline(true);
            this.setOutput(true, "Boolean");
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip("Igual a");
        }
    };

    // y (and)
    Blockly.Blocks['calvin_operator_and'] = {
        init: function() {
            this.appendValueInput("A").setCheck("Boolean").appendField("");
            this.appendDummyInput().appendField("y");
            this.appendValueInput("B").setCheck("Boolean").appendField("");
            this.setInputsInline(true);
            this.setOutput(true, "Boolean");
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip("Verdadero si ambas condiciones son verdaderas");
        }
    };

    // o (or)
    Blockly.Blocks['calvin_operator_or'] = {
        init: function() {
            this.appendValueInput("A").setCheck("Boolean").appendField("");
            this.appendDummyInput().appendField("o");
            this.appendValueInput("B").setCheck("Boolean").appendField("");
            this.setInputsInline(true);
            this.setOutput(true, "Boolean");
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip("Verdadero si al menos una condición es verdadera");
        }
    };

    // raíz cuadrada de
    Blockly.Blocks['calvin_operator_sqrt'] = {
        init: function() {
            this.appendValueInput("X")
                .setCheck("Number")
                .appendField("raíz cuadrada de");
            this.setOutput(true, "Number");
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip("Calcula la raíz cuadrada");
        }
    };

    // calvin_operator_compare (general, con dropdown)
    Blockly.Blocks['calvin_operator_compare'] = {
        init: function() {
            this.appendValueInput("A").setCheck(null).appendField("");
            this.appendDummyInput()
                .appendField(new Blockly.FieldDropdown([
                    ["=", "EQ"], ["≠", "NEQ"], ["<", "LT"], ["≤", "LTE"],
                    [">", "GT"], ["≥", "GTE"]
                ]), "OP");
            this.appendValueInput("B").setCheck(null).appendField("");
            this.setInputsInline(true);
            this.setOutput(true, "Boolean");
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip("Compara dos valores");
        }
    };

    // ============================================
    // calvin_text_* - Texto
    // ============================================

    // texto literal
    Blockly.Blocks['calvin_text_string'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('"')
                .appendField(new Blockly.FieldTextInput("texto"), "TEXT")
                .appendField('"');
            this.setOutput(true, "String");
            this.setColour(COLOUR_TEXT);
            this.setTooltip("Un texto literal");
        }
    };

    Blockly.Blocks['calvin_text_concat'] = {
        init: function() {
            this.appendValueInput("A").setCheck("String").appendField("Texto A");
            this.appendValueInput("B").setCheck("String").appendField("Texto B");
            this.setOutput(true, "String");
            this.setColour(COLOUR_TEXT);
            this.setTooltip("Concatena dos textos");
        }
    };

    // ============================================
    // calvin_serial_* - Serial
    // ============================================

    // 1) Inicializar Serial [baud]
    Blockly.Blocks['calvin_serial_begin'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Inicializar Serial")
                .appendField(new Blockly.FieldDropdown([
                    ["9600", "9600"],
                    ["115200", "115200"],
                    ["57600", "57600"],
                    ["38400", "38400"],
                    ["19200", "19200"],
                    ["4800", "4800"]
                ]), "BAUD");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_SERIAL);
            this.setTooltip("Inicia la comunicación serial");
        }
    };

    // 2) Serial tiempo de espera [n]
    Blockly.Blocks['calvin_serial_set_timeout'] = {
        init: function() {
            this.appendValueInput("MS")
                .setCheck("Number")
                .appendField("Serial tiempo de espera");
            this.appendDummyInput().appendField("ms");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_SERIAL);
            this.setTooltip("Establece el tiempo de espera para lectura serial (ms)");
        }
    };

    // 3) Serial Print [valor]
    Blockly.Blocks['calvin_serial_print'] = {
        init: function() {
            this.appendValueInput("VALUE")
                .setCheck(null)
                .appendField("Serial Print");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_SERIAL);
            this.setTooltip("Imprime un valor en el monitor serial");
        }
    };

    // 4) Hay datos en el puerto serial (boolean)
    Blockly.Blocks['calvin_serial_has_data'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Hay datos en el puerto serial");
            this.setOutput(true, "Boolean");
            this.setColour(COLOUR_SERIAL);
            this.setTooltip("Verdadero si hay datos disponibles para leer");
        }
    };

    // 5) Datos del puerto serial (lee string)
    Blockly.Blocks['calvin_serial_read_string'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Datos del puerto serial");
            this.setOutput(true, "String");
            this.setColour(COLOUR_SERIAL);
            this.setTooltip("Lee los datos como texto desde el puerto serial");
        }
    };

    // ============================================
    // calvin_ble_* - Bluetooth Low Energy (solo ESP32)
    // ============================================

    // 1) Inicializar BLE - Nombre, Conectado, Desconectado, Servicios
    Blockly.Blocks['calvin_ble_init'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("📶 Inicializar BLE")
                .appendField(new Blockly.FieldTextInput("CalvinBot"), "NAME");
            this.appendStatementInput("CONNECTED")
                .appendField("Conectado");
            this.appendStatementInput("DISCONNECTED")
                .appendField("Desconectado");
            this.appendStatementInput("SERVICES")
                .appendField("Servicios");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BLE);
            this.setTooltip("Inicializa BLE con nombre. Solo compatible con ESP32.");
        }
    };

    // 2) Servicio [UUID] ... Características ... (anidar dentro de Inicializar BLE)
    Blockly.Blocks['calvin_ble_service'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Servicio")
                .appendField(new Blockly.FieldTextInput("4fafc201-1fb5-459e-8fcc-c5c9c331914b"), "UUID");
            this.appendStatementInput("CHARACTERISTICS")
                .appendField("Características");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BLE);
            this.setTooltip("Define un servicio BLE con UUID. Añade características dentro.");
        }
    };

    // 3) Característica [UUID] ... Hacer ... (anidar dentro de Servicio)
    Blockly.Blocks['calvin_ble_characteristic'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Característica")
                .appendField(new Blockly.FieldTextInput("beb5483e-36e1-4688-b7f5-ea07361b26a8"), "UUID")
                .appendField("id")
                .appendField(new Blockly.FieldTextInput("cmd"), "NAME");
            this.appendStatementInput("DO")
                .appendField("cuando escriben, hacer");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BLE);
            this.setTooltip("Define una característica BLE. El id se usa en BLE escribir.");
        }
    };

    // 4) ble write [característica] [valor]
    Blockly.Blocks['calvin_ble_write'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("📶 BLE escribir característica")
                .appendField(new Blockly.FieldTextInput("cmd"), "CHAR");
            this.appendValueInput("VALUE")
                .setCheck(null)
                .appendField("valor");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BLE);
            this.setTooltip("Escribe un valor en la característica BLE (envía al cliente). Solo ESP32.");
        }
    };

    // 5) Valor numérico de esta característica (usar dentro del callback de característica)
    Blockly.Blocks['calvin_ble_char_value_number'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("valor numérico de esta característica");
            this.setOutput(true, "Number");
            this.setColour(COLOUR_BLE);
            this.setTooltip("Devuelve el valor numérico que el cliente escribió en esta característica.");
        }
    };

    // 6) Valor string de esta característica
    Blockly.Blocks['calvin_ble_char_value_string'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("valor string de esta característica");
            this.setOutput(true, "String");
            this.setColour(COLOUR_BLE);
            this.setTooltip("Devuelve el valor texto que el cliente escribió en esta característica.");
        }
    };

    // ============================================
    // calvin_io_* - Entrada/Salida (IN/OUT)
    // ============================================

    // 1) HIGH / LOW - valor constante
    Blockly.Blocks['calvin_io_high_low'] = {
        init: function() {
            this.appendDummyInput()
                .appendField(new Blockly.FieldDropdown([["HIGH", "HIGH"], ["LOW", "LOW"]]), "VAL");
            this.setOutput(true, "Number");
            this.setColour(COLOUR_IO);
            this.setTooltip("Devuelve HIGH o LOW");
        }
    };

    // 2) DigitalWrite PIN# [pin] Estado [HIGH/LOW]
    Blockly.Blocks['calvin_io_digital_write'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("DigitalWrite pin")
                .appendField(new Blockly.FieldNumber(13, 0, 255), "PIN");
            this.appendValueInput("STAT")
                .setCheck(null)
                .appendField("estado");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_IO);
            this.setTooltip("Escribe HIGH o LOW en un pin digital");
        }
    };

    // 3) DigitalRead PIN# [pin]
    Blockly.Blocks['calvin_io_digital_read'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("DigitalRead pin")
                .appendField(new Blockly.FieldNumber(2, 0, 255), "PIN");
            this.setOutput(true, "Number");
            this.setColour(COLOUR_IO);
            this.setTooltip("Lee el valor digital de un pin (HIGH/LOW)");
        }
    };

    // 4) AnalogRead PIN# [pin] (A0-A5 típico)
    Blockly.Blocks['calvin_io_analog_read'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("AnalogRead pin A")
                .appendField(new Blockly.FieldNumber(0, 0, 15), "PIN");
            this.setOutput(true, "Number");
            this.setColour(COLOUR_IO);
            this.setTooltip("Lee el valor analógico (0-1023) del pin A");
        }
    };

    // 5) AnalogWrite PIN# [pin] [valor]
    Blockly.Blocks['calvin_io_analog_write'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("AnalogWrite pin")
                .appendField(new Blockly.FieldNumber(9, 0, 255), "PIN");
            this.appendValueInput("VALUE")
                .setCheck("Number")
                .appendField("valor");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_IO);
            this.setTooltip("Escribe un valor PWM (0-255) en un pin");
        }
    };

    // ============================================
    // calvin_func_* - Funciones (con mutador: input name, allow statements)
    // ============================================

    // Bloques para el mutador (solo aparecen en el popup de la tuerca)
    Blockly.Blocks['calvin_func_mutatorarg'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("input name:")
                .appendField(new Blockly.FieldTextInput("x"), "NAME");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_FUNC);
            this.setTooltip("Parámetro de la función. Arrastra aquí para añadir.");
        }
    };

    Blockly.Blocks['calvin_func_mutator'] = {
        init: function() {
            this.appendDummyInput()
                .appendField(new Blockly.FieldCheckbox(true), "ALLOW_STATEMENTS")
                .appendField("allow statements");
            this.appendStatementInput("INPUTS")
                .appendField("inputs");
            this.setColour(COLOUR_FUNC);
            this.setTooltip("Configuración de la función");
        }
    };

    const CALVIN_FUNC_MUTATOR = {
        paramNames_: [],
        allowStatements_: true,

        saveExtraState: function() {
            return {
                paramNames: this.paramNames_,
                allowStatements: this.allowStatements_
            };
        },
        loadExtraState: function(state) {
            this.paramNames_ = state && state.paramNames ? state.paramNames : [];
            this.allowStatements_ = state && state.allowStatements !== undefined ? state.allowStatements : true;
            this.updateShape_();
        },
        mutationToDom: function() {
            const container = Blockly.utils.xml.createElement('mutation');
            container.setAttribute('allowstatements', this.allowStatements_ ? '1' : '0');
            this.paramNames_.forEach(function(name) {
                const arg = Blockly.utils.xml.createElement('arg');
                arg.setAttribute('name', name);
                container.appendChild(arg);
            });
            return container;
        },
        domToMutation: function(xmlElement) {
            this.allowStatements_ = xmlElement.getAttribute('allowstatements') !== '0';
            this.paramNames_ = [];
            const args = xmlElement.getElementsByTagName('arg');
            for (let i = 0; i < args.length; i++) {
                this.paramNames_.push(args[i].getAttribute('name') || 'x');
            }
            this.updateShape_();
        },
        decompose: function(workspace) {
            const container = workspace.newBlock('calvin_func_mutator');
            container.initSvg();
            let connection = container.getInput('INPUTS').connection;
            for (let i = 0; i < this.paramNames_.length; i++) {
                const argBlock = workspace.newBlock('calvin_func_mutatorarg');
                argBlock.setFieldValue(this.paramNames_[i] || 'x', 'NAME');
                argBlock.initSvg();
                connection.connect(argBlock.previousConnection);
                connection = argBlock.nextConnection;
            }
            container.setFieldValue(this.allowStatements_, 'ALLOW_STATEMENTS');
            return container;
        },
        compose: function(containerBlock) {
            this.allowStatements_ = containerBlock.getFieldValue('ALLOW_STATEMENTS');
            this.paramNames_ = [];
            let argBlock = containerBlock.getInputTargetBlock('INPUTS');
            while (argBlock && !argBlock.isInsertionMarker()) {
                this.paramNames_.push(argBlock.getFieldValue('NAME') || 'x');
                argBlock = argBlock.getNextBlock();
            }
            this.updateShape_();
        },
        saveConnections: function() {},
        updateShape_: function() {
            if (this.getInput('PARAMS_LABEL')) {
                this.removeInput('PARAMS_LABEL');
            }
            if (this.paramNames_.length > 0) {
                this.appendDummyInput('PARAMS_LABEL')
                    .appendField('with:')
                    .appendField(this.paramNames_.join(', '));
                this.moveInputBefore('PARAMS_LABEL', 'STUFF');
            }
            if (this.getInput('STUFF')) {
                this.getInput('STUFF').setVisible(this.allowStatements_);
            }
        }
    };

    const calvinFuncMutatorHelper = function() {
        if (this.paramNames_ === undefined) this.paramNames_ = [];
        if (this.allowStatements_ === undefined) this.allowStatements_ = true;
    };
    Blockly.Extensions.registerMutator('calvin_func_mutator', CALVIN_FUNC_MUTATOR, calvinFuncMutatorHelper, ['calvin_func_mutatorarg']);

    // 1) Función sin retorno (void) - como original "to [do something]" con mutador
    Blockly.Blocks['calvin_func_defnoreturn'] = {
        hasReturnType: false,
        init: function() {
            this.appendDummyInput()
                .appendField("función")
                .appendField(new Blockly.FieldTextInput("do something"), "NAME");
            this.appendStatementInput("STUFF")
                .appendField("hacer");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_FUNC);
            this.setTooltip("Define una función. Usa la tuerca para añadir parámetros.");
        }
    };
    Blockly.Blocks['calvin_func_defnoreturn'].mutator = 'calvin_func_mutator';

    // 2) Función con retorno - como original "to [do something2]" con return y mutador
    Blockly.Blocks['calvin_func_defreturn'] = {
        hasReturnType: true,
        init: function() {
            this.appendDummyInput()
                .appendField("función")
                .appendField(new Blockly.FieldTextInput("do something2"), "NAME")
                .appendField("retorna")
                .appendField(new Blockly.FieldDropdown([
                    ["número (int)", "int"],
                    ["decimal (float)", "float"],
                    ["texto (String)", "String"]
                ]), "RETURN_TYPE");
            this.appendStatementInput("STUFF")
                .appendField("hacer");
            this.appendValueInput("RETURN")
                .setCheck(null)
                .appendField("devolver");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_FUNC);
            this.setTooltip("Define una función que devuelve un valor. Usa la tuerca para parámetros.");
        }
    };
    Blockly.Blocks['calvin_func_defreturn'].mutator = 'calvin_func_mutator';

    // 3) Si [condición] return [valor] - early return (usar dentro de función con retorno)
    Blockly.Blocks['calvin_func_ifreturn'] = {
        init: function() {
            this.appendValueInput("CONDITION")
                .setCheck("Boolean")
                .appendField("si");
            this.appendValueInput("VALUE")
                .setCheck(null)
                .appendField("return");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_FUNC);
            this.setTooltip("Si la condición es verdadera, devuelve el valor y sale de la función");
        }
    };

    // Mutador para bloques de llamada (argumentos)
    Blockly.Blocks['calvin_func_call_mutatorarg'] = {
        init: function() {
            this.appendDummyInput().appendField("arg");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_FUNC);
        }
    };

    Blockly.Blocks['calvin_func_call_mutator'] = {
        init: function() {
            this.appendStatementInput("INPUTS").appendField("args");
            this.setColour(COLOUR_FUNC);
        }
    };

    const CALVIN_FUNC_CALL_MUTATOR = {
        argCount_: 0,
        saveExtraState: function() { return { argCount: this.argCount_ }; },
        loadExtraState: function(s) { this.argCount_ = (s && s.argCount) | 0; this.updateShape_(); },
        mutationToDom: function() {
            const m = Blockly.utils.xml.createElement('mutation');
            m.setAttribute('argcount', this.argCount_);
            return m;
        },
        domToMutation: function(x) { this.argCount_ = parseInt(x.getAttribute('argcount'), 10) || 0; this.updateShape_(); },
        decompose: function(ws) {
            const c = ws.newBlock('calvin_func_call_mutator');
            c.initSvg();
            let conn = c.getInput('INPUTS').connection;
            for (let i = 0; i < this.argCount_; i++) {
                const b = ws.newBlock('calvin_func_call_mutatorarg');
                b.initSvg();
                conn.connect(b.previousConnection);
                conn = b.nextConnection;
            }
            return c;
        },
        compose: function(top) {
            let n = 0;
            let b = top.getInputTargetBlock('INPUTS');
            while (b && !b.isInsertionMarker()) { n++; b = b.getNextBlock(); }
            const conns = [];
            b = top.getInputTargetBlock('INPUTS');
            while (b && !b.isInsertionMarker()) {
                conns.push(b.argConnection_);
                b = b.getNextBlock();
            }
            for (let i = 0; i < this.argCount_; i++) {
                const c = this.getInput('ARG' + i) && this.getInput('ARG' + i).connection.targetConnection;
                if (c && conns.indexOf(c) === -1) c.disconnect();
            }
            this.argCount_ = n;
            this.updateShape_();
            for (let i = 0; i < n; i++) {
                if (conns[i]) conns[i].reconnect(this, 'ARG' + i);
            }
        },
        saveConnections: function(top) {
            let i = 0;
            let b = top.getInputTargetBlock('INPUTS');
            while (b && !b.isInsertionMarker()) {
                const inp = this.getInput('ARG' + i);
                b.argConnection_ = inp && inp.connection.targetConnection;
                i++;
                b = b.getNextBlock();
            }
        },
        updateShape_: function() {
            let i = 0;
            while (this.getInput('ARG' + i)) this.removeInput('ARG' + i), i++;
            for (i = 0; i < this.argCount_; i++) {
                this.appendValueInput('ARG' + i).appendField('arg' + (i + 1));
            }
        }
    };

    const calvinCallMutatorHelper = function() {
        if (this.argCount_ === undefined) this.argCount_ = 0;
    };
    Blockly.Extensions.registerMutator('calvin_func_call_mutator', CALVIN_FUNC_CALL_MUTATOR, calvinCallMutatorHelper, ['calvin_func_call_mutatorarg']);

    // Llamar función (sin retorno) - con mutador para argumentos
    Blockly.Blocks['calvin_func_call'] = {
        init: function() {
            this.appendDummyInput()
                .appendField(new Blockly.FieldTextInput("do something"), "NAME");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_FUNC);
            this.setTooltip("Llama a una función. Usa la tuerca para añadir argumentos.");
        }
    };
    Blockly.Blocks['calvin_func_call'].mutator = 'calvin_func_call_mutator';

    // Llamar función con retorno - con mutador para argumentos
    Blockly.Blocks['calvin_func_call_return'] = {
        init: function() {
            this.appendDummyInput()
                .appendField(new Blockly.FieldTextInput("do something2"), "NAME");
            this.setOutput(true, null);
            this.setColour(COLOUR_FUNC);
            this.setTooltip("Llama a una función y usa el valor. Usa la tuerca para argumentos.");
        }
    };
    Blockly.Blocks['calvin_func_call_return'].mutator = 'calvin_func_call_mutator';

    // ============================================
    // calvin_var_* - Variables (reutiliza arduino_get/set, añade labels tipo)
    // ============================================
    Blockly.Blocks['calvin_var_set'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("📝 Asignar variable")
                .appendField(new Blockly.FieldTextInput("item"), "VAR");
            this.appendValueInput("VALUE").setCheck(null).appendField("=");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_VAR);
            this.setTooltip("Asigna un valor a una variable");
        }
    };

    // ============================================
    // calvin_botflow1_* - BotFlow Nivel 1 (Hardware Calvin)
    // ============================================

    Blockly.Blocks['calvin_botflow1_step'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("🤖 BotFlow1 - Paso")
                .appendField(new Blockly.FieldNumber(1, 0, 99), "STEP");
            this.appendStatementInput("DO").setCheck(null).appendField("hacer");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Paso de secuencia BotFlow Nivel 1");
        }
    };

    // 1) Inicializar sensor de proximidad
    Blockly.Blocks['calvin_botflow1_init_proximidad'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Inicializar sensor de proximidad");
            this.appendDummyInput()
                .appendField("TRIG")
                .appendField(new Blockly.FieldNumber(18, 0, 255), "TRIG")
                .appendField("ECHO")
                .appendField(new Blockly.FieldNumber(36, 0, 255), "ECHO");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Configura el sensor ultrasónico de proximidad");
        }
    };

    // 2) distancia [cm]
    Blockly.Blocks['calvin_botflow1_distancia'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("distancia")
                .appendField("cm");
            this.setOutput(true, "Number");
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Devuelve la distancia al obstáculo en centímetros");
        }
    };

    // 3) Inicializar Nota Musical
    Blockly.Blocks['calvin_botflow1_init_nota'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Inicializar Nota Musical");
            this.appendDummyInput()
                .appendField("pin")
                .appendField(new Blockly.FieldNumber(3, 0, 255), "PIN");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Configura el buzzer para notas musicales");
        }
    };

    // 4) Nota [nota] octava [n] durante [duración] seg (como original: octava 0, inf)
    Blockly.Blocks['calvin_botflow1_nota_octava'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Nota")
                .appendField(new Blockly.FieldDropdown([
                    ["Do", "DO"], ["Re", "RE"], ["Mi", "MI"], ["Fa", "FA"],
                    ["Sol", "SOL"], ["La", "LA"], ["Si", "SI"]
                ]), "NOTA")
                .appendField("octava")
                .appendField(new Blockly.FieldNumber(0, 0, 5), "OCTAVA")
                .appendField("durante");
            this.appendDummyInput()
                .appendField(new Blockly.FieldDropdown([
                    ["0.5 seg", "0.5"], ["1 seg", "1"], ["2 seg", "2"], ["5 seg", "5"],
                    ["inf seg", "inf"]
                ]), "DURACION");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Reproduce una nota musical durante X segundos (inf = hasta siguiente bloque)");
        }
    };

    // 5) Inicializar led RGB tipo [A] (como original: solo tipo, pines por defecto)
    Blockly.Blocks['calvin_botflow1_init_rgb'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Inicializar led RGB tipo")
                .appendField(new Blockly.FieldDropdown([
                    ["A", "A"],
                    ["C", "C"]
                ]), "TIPO");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Configura LED RGB tipo A (ánodo común) o C (cátodo común). Pines R=5, G=6, B=11");
        }
    };

    // 6) Encender led [color] durante [duración] seg (como original: Rojo, inf)
    Blockly.Blocks['calvin_botflow1_led_color'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Encender led");
            this.appendDummyInput()
                .appendField(new Blockly.FieldDropdown([
                    ["Rojo", "rojo"],
                    ["Verde", "verde"],
                    ["Azul", "azul"],
                    ["Amarillo", "amarillo"],
                    ["Cyan", "cyan"],
                    ["Magenta", "magenta"],
                    ["Blanco", "blanco"]
                ]), "COLOR");
            this.appendDummyInput()
                .appendField("durante")
                .appendField(new Blockly.FieldDropdown([
                    ["0.5 seg", "0.5"], ["1 seg", "1"], ["2 seg", "2"], ["5 seg", "5"],
                    ["inf", "inf"]
                ]), "DURACION");
            this.appendDummyInput().appendField("seg");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Enciende el LED RGB durante X segundos (inf = hasta siguiente bloque)");
        }
    };

    // 7) Inicializar Motores 220 PWM (como original BotFlow)
    Blockly.Blocks['calvin_botflow1_init_motores'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Inicializar Motores")
                .appendField(new Blockly.FieldNumber(220, 0, 255), "PWM")
                .appendField("PWM");
            this.appendDummyInput()
                .appendField("izq")
                .appendField(new Blockly.FieldNumber(9, 0, 255), "IZQ")
                .appendField("der")
                .appendField(new Blockly.FieldNumber(10, 0, 255), "DER");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Configura motores del robot. PWM 0-255 (220 por defecto como original). Pines izq=9, der=10");
        }
    };

    // 8) ir Adelante durante [seg]
    Blockly.Blocks['calvin_botflow1_adelante'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("ir Adelante durante");
            this.appendValueInput("SEG")
                .setCheck("Number")
                .appendField("");
            this.appendDummyInput().appendField("seg");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Avanza durante X segundos");
        }
    };

    // 9) Girar Motor [izquierdo/derecho] en sentido [Horario/Antihorario] (como original)
    Blockly.Blocks['calvin_botflow1_girar_motor'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Girar Motor")
                .appendField(new Blockly.FieldDropdown([
                    ["izquierdo", "0"],
                    ["derecho", "1"]
                ]), "LADO")
                .appendField("en sentido")
                .appendField(new Blockly.FieldDropdown([
                    ["Horario", "0"],
                    ["Antihorario", "1"]
                ]), "SENTIDO")
                .appendField("durante");
            this.appendValueInput("SEG")
                .setCheck("Number")
                .appendField("");
            this.appendDummyInput().appendField("seg");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Gira un motor en la dirección indicada durante X segundos");
        }
    };

    // ============================================
    // calvin_botflow2_* - BotFlow Nivel 2 (sensores de línea)
    // ============================================

    Blockly.Blocks['calvin_botflow2_condition'] = {
        init: function() {
            this.appendValueInput("COND").setCheck("Boolean").appendField("🤖 BotFlow2 - Si");
            this.appendStatementInput("DO").setCheck(null).appendField("entonces");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW2);
            this.setTooltip("Condición BotFlow Nivel 2");
        }
    };

    const LADO_OPTIONS = [
        ["Izquierdo", "0"],
        ["Centro", "1"],
        ["Derecho", "2"]
    ];

    // 1) Inicializar sensores de línea
    Blockly.Blocks['calvin_botflow2_init_lineas'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Inicializar sensores de línea");
            this.appendDummyInput()
                .appendField("izq A")
                .appendField(new Blockly.FieldNumber(0, 0, 7), "IZQ")
                .appendField("centro A")
                .appendField(new Blockly.FieldNumber(1, 0, 7), "CENT")
                .appendField("der A")
                .appendField(new Blockly.FieldNumber(2, 0, 7), "DER");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW2);
            this.setTooltip("Configura los sensores de línea (pines analógicos A0-A7)");
        }
    };

    // 2) Calibrar sensores de línea durante [n] lecturas
    Blockly.Blocks['calvin_botflow2_calibrar_lineas'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Calibrar sensores de línea durante");
            this.appendValueInput("N")
                .setCheck("Number")
                .appendField("");
            this.appendDummyInput().appendField("lecturas");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW2);
            this.setTooltip("Realiza n lecturas para calibrar min/max de cada sensor");
        }
    };

    // 3) Valor sensor de línea [lado]
    Blockly.Blocks['calvin_botflow2_linea_valor'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Valor sensor de línea")
                .appendField(new Blockly.FieldDropdown(LADO_OPTIONS), "LADO");
            this.setOutput(true, "Number");
            this.setColour(COLOUR_BOTFLOW2);
            this.setTooltip("Devuelve el valor analógico (0-1023) del sensor");
        }
    };

    // 4) Valor umbral sensor de línea [lado]
    Blockly.Blocks['calvin_botflow2_linea_umbral'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Valor umbral sensor de línea")
                .appendField(new Blockly.FieldDropdown(LADO_OPTIONS), "LADO");
            this.setOutput(true, "Number");
            this.setColour(COLOUR_BOTFLOW2);
            this.setTooltip("Devuelve el umbral calibrado (min+max)/2 del sensor");
        }
    };

})();
