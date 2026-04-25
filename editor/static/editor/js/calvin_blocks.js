/**
 * Bloques Calvin - Familia técnica separada
 * Naming: base_delay, switch_case, case, controls_* (Botflow), procedures_defnoreturn/procedures_defreturn/procedures_ifreturn (Botflow funciones), sumar/restar/.../math_single (Botflow), calvin_operator_*, calvin_text_*, serial_* (Botflow), inout_* (Botflow I/O), etc.
 * Extensión de MAX-IDE; no modifica max_* ni arduino_*
 */

(function() {
    'use strict';

    if (typeof Blockly === 'undefined') return;

    /** Control Calvin (delay, switch, bucles Botflow, si/sino, logic_*): azul unificado */
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
    // Control de flujo (Botflow)
    // ============================================

    // BotFlow: base_delay — Esperar [DELAY_TIME] ms.
    Blockly.Blocks['base_delay'] = {
        init: function() {
            this.appendDummyInput().appendField('Esperar');
            this.appendValueInput('DELAY_TIME').setCheck('Number');
            this.appendDummyInput().appendField('ms.');
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_CONTROL);
            this.setTooltip('delay(ms). Compatible con XML Botflow (DELAY_TIME).');
        }
    };

    // BotFlow: switch_case — VARIABLE + CASES (Sea…) + DEFAULT ("Si nada se cumple")
    Blockly.Blocks['switch_case'] = {
        init: function() {
            this.appendValueInput('VARIABLE').setCheck(null).appendField('En caso de que');
            this.appendStatementInput('CASES').setCheck(null);
            this.appendStatementInput('DEFAULT').setCheck(null).appendField('Si nada se cumple');
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_CONTROL);
            this.setTooltip('switch (VARIABLE). CASES: bloques case (Sea… Hacer…). DEFAULT: rama si no coincide ningún caso.');
        }
    };

    // BotFlow: case — Sea [VALUE] Hacer [DO]
    Blockly.Blocks['case'] = {
        init: function() {
            this.appendValueInput('VALUE').setCheck(null).appendField('Sea');
            this.appendStatementInput('DO').setCheck(null).appendField('Hacer');
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_CONTROL);
            this.setTooltip('Caso del switch (Botflow: case).');
        }
    };

    // BotFlow: controls_whileUntil — repetir [mientras|hasta] BOOL … hacer … (misma fila superior que Botflow)
    Blockly.Blocks['controls_whileUntil'] = {
        init: function() {
            this.appendValueInput('BOOL').setCheck('Boolean')
                .appendField('repetir')
                .appendField(new Blockly.FieldDropdown([
                    ['mientras', 'WHILE'],
                    ['hasta', 'UNTIL']
                ]), 'MODE');
            this.appendStatementInput('DO').setCheck(null).appendField('hacer');
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_CONTROL);
            this.setTooltip('while / repeat-until (Botflow). MODE: WHILE o UNTIL.');
        }
    };

    // BotFlow: controls_for — contar [VAR] de FROM a TO añadiendo BY hacer … (FieldVariable)
    Blockly.Blocks['controls_for'] = {
        init: function() {
            this.appendValueInput('FROM').setCheck('Number')
                .appendField('contar')
                .appendField(new Blockly.FieldVariable(null), 'VAR')
                .appendField('de');
            this.appendValueInput('TO').setCheck('Number').appendField('a');
            this.appendValueInput('BY').setCheck('Number').appendField('añadiendo');
            this.appendStatementInput('DO').setCheck(null).appendField('hacer');
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_CONTROL);
            this.setTooltip('Bucle for con variable de Blockly (Botflow controls_for).');
        }
    };

    // BotFlow: controls_if — sí [IF0] entonces [DO0] (solo una rama; distinto de controls_ifelse)
    Blockly.Blocks['controls_if'] = {
        init: function() {
            this.appendValueInput('IF0').setCheck('Boolean').appendField('sí');
            this.appendStatementInput('DO0').setCheck(null).appendField('entonces');
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_CONTROL);
            this.setTooltip('if (Botflow): sí condición entonces …');
        }
    };

    // BotFlow: controls_ifelse — sí IF0 entonces DO0 si no ELSE
    Blockly.Blocks['controls_ifelse'] = {
        init: function() {
            this.appendValueInput('IF0').setCheck('Boolean').appendField('sí');
            this.appendStatementInput('DO0').setCheck(null).appendField('entonces');
            this.appendStatementInput('ELSE').setCheck(null).appendField('si no');
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_CONTROL);
            this.setTooltip('if / else (Botflow): sí … entonces … si no …');
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

    // BotFlow: sumar — A [+] B (sombras math_number en importación XML)
    Blockly.Blocks['sumar'] = {
        init: function() {
            this.appendValueInput('A').setCheck(null);
            this.appendDummyInput().appendField('+');
            this.appendValueInput('B').setCheck(null);
            this.setInputsInline(true);
            this.setOutput(true, 'Number');
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip('Suma A + B (Botflow: sumar)');
        }
    };

    // BotFlow: restar — A [−] B (sombras math_number en importación XML)
    Blockly.Blocks['restar'] = {
        init: function() {
            this.appendValueInput('A').setCheck(null);
            this.appendDummyInput().appendField('-');
            this.appendValueInput('B').setCheck(null);
            this.setInputsInline(true);
            this.setOutput(true, 'Number');
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip('Resta A - B (Botflow: restar)');
        }
    };

    // BotFlow: multiplicar — A [*] B (sombras math_number en importación XML)
    Blockly.Blocks['multiplicar'] = {
        init: function() {
            this.appendValueInput('A').setCheck(null);
            this.appendDummyInput().appendField('*');
            this.appendValueInput('B').setCheck(null);
            this.setInputsInline(true);
            this.setOutput(true, 'Number');
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip('Multiplica A * B (Botflow: multiplicar)');
        }
    };

    // BotFlow: dividir — A [/] B (sombras math_number en importación XML)
    Blockly.Blocks['dividir'] = {
        init: function() {
            this.appendValueInput('A').setCheck(null);
            this.appendDummyInput().appendField('/');
            this.appendValueInput('B').setCheck(null);
            this.setInputsInline(true);
            this.setOutput(true, 'Number');
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip('Divide A / B (Botflow: dividir)');
        }
    };

    // BotFlow: math_random_int — FROM / TO (sombras math_number; mismas etiquetas que calvin_operator_random)
    Blockly.Blocks['math_random_int'] = {
        init: function() {
            this.appendValueInput('FROM').setCheck(null).appendField('número aleatorio entre');
            this.appendValueInput('TO').setCheck(null).appendField('y');
            this.setInputsInline(true);
            this.setOutput(true, 'Number');
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip('Entero aleatorio entre FROM y TO (inclusivo) (Botflow: math_random_int)');
        }
    };

    // BotFlow: mayor_que — A [>] B (sombras math_number; misma lógica que calvin_operator_gt)
    Blockly.Blocks['mayor_que'] = {
        init: function() {
            this.appendValueInput('A').setCheck(null);
            this.appendDummyInput().appendField('>');
            this.appendValueInput('B').setCheck(null);
            this.setInputsInline(true);
            this.setOutput(true, 'Boolean');
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip('Verdadero si A > B (Botflow: mayor_que)');
        }
    };

    // BotFlow: menor_que — A [<] B (sombras math_number; misma lógica que calvin_operator_lt)
    Blockly.Blocks['menor_que'] = {
        init: function() {
            this.appendValueInput('A').setCheck(null);
            this.appendDummyInput().appendField('<');
            this.appendValueInput('B').setCheck(null);
            this.setInputsInline(true);
            this.setOutput(true, 'Boolean');
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip('Verdadero si A < B (Botflow: menor_que)');
        }
    };

    // BotFlow: igual_que — A [=] B (sombras math_number; misma lógica que calvin_operator_eq)
    Blockly.Blocks['igual_que'] = {
        init: function() {
            this.appendValueInput('A').setCheck(null);
            this.appendDummyInput().appendField('=');
            this.appendValueInput('B').setCheck(null);
            this.setInputsInline(true);
            this.setOutput(true, 'Boolean');
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip('Verdadero si A == B (Botflow: igual_que)');
        }
    };

    // BotFlow: logica_y — A [y] B (misma lógica que calvin_operator_and)
    Blockly.Blocks['logica_y'] = {
        init: function() {
            this.appendValueInput('A').setCheck(null);
            this.appendDummyInput().appendField('y');
            this.appendValueInput('B').setCheck(null);
            this.setInputsInline(true);
            this.setOutput(true, 'Boolean');
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip('Verdadero si A y B son verdaderos (Botflow: logica_y)');
        }
    };

    // BotFlow: logica_o — A [o] B (misma lógica que calvin_operator_or)
    Blockly.Blocks['logica_o'] = {
        init: function() {
            this.appendValueInput('A').setCheck(null);
            this.appendDummyInput().appendField('o');
            this.appendValueInput('B').setCheck(null);
            this.setInputsInline(true);
            this.setOutput(true, 'Boolean');
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip('Verdadero si A o B es verdadero (Botflow: logica_o)');
        }
    };

    // BotFlow: math_single — dropdown OP en la fila NUM (p. ej. ROOT = raíz cuadrada)
    Blockly.Blocks['math_single'] = {
        init: function() {
            this.appendValueInput('NUM')
                .setCheck(null)
                .appendField(new Blockly.FieldDropdown([
                    ['raíz cuadrada de', 'ROOT']
                ]), 'OP');
            this.setOutput(true, 'Number');
            this.setColour(COLOUR_OPERATOR);
            this.setTooltip('Operación sobre un número (Botflow: math_single)');
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

    // BotFlow / Blockly: logic_compare — A OP B (mismos valores OP que Blockly estándar)
    Blockly.Blocks['logic_compare'] = {
        init: function() {
            this.appendValueInput('A').setCheck(null).appendField('');
            this.appendDummyInput()
                .appendField(new Blockly.FieldDropdown([
                    ['=', 'EQ'], ['≠', 'NEQ'], ['<', 'LT'], ['≤', 'LTE'],
                    ['>', 'GT'], ['≥', 'GTE']
                ]), 'OP');
            this.appendValueInput('B').setCheck(null).appendField('');
            this.setInputsInline(true);
            this.setOutput(true, 'Boolean');
            this.setColour(COLOUR_CONTROL);
            this.setTooltip('Comparación (Botflow logic_compare)');
        }
    };

    // BotFlow / Blockly: logic_negate — etiqueta «sí» como en Botflow; código generado sigue siendo !(BOOL)
    Blockly.Blocks['logic_negate'] = {
        init: function() {
            this.appendValueInput('BOOL')
                .setCheck(null)
                .appendField('sí');
            this.setOutput(true, 'Boolean');
            this.setColour(COLOUR_CONTROL);
            this.setTooltip('logic_negate: genera !(condición).');
        }
    };

    // BotFlow / Blockly: logic_operation — A OP B (etiquetas AND/OR; valores XML: AND|OR)
    Blockly.Blocks['logic_operation'] = {
        init: function() {
            this.appendValueInput('A').setCheck(null).appendField('');
            this.appendDummyInput()
                .appendField(new Blockly.FieldDropdown([
                    ['AND', 'AND'],
                    ['OR', 'OR']
                ]), 'OP');
            this.appendValueInput('B').setCheck(null).appendField('');
            this.setInputsInline(true);
            this.setOutput(true, 'Boolean');
            this.setColour(COLOUR_CONTROL);
            this.setTooltip('AND / OR (Botflow logic_operation)');
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
    // Serial (tipos Botflow: serial_*)
    // ============================================

    // BotFlow: serial_init — valor BADURATE (nombre original con typo), sombra math_number
    Blockly.Blocks['serial_init'] = {
        init: function() {
            this.appendValueInput('BADURATE')
                .setCheck('Number')
                .appendField('Inicializar Serial');
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_SERIAL);
            this.setTooltip('Serial.begin(baudios). Compatible con XML Botflow (BADURATE).');
        }
    };

    // BotFlow: serial_timeout — Serial.setTimeout(ms), entrada TIMEOUT
    Blockly.Blocks['serial_timeout'] = {
        init: function() {
            this.appendValueInput('TIMEOUT')
                .setCheck('Number')
                .appendField('Serial tiempo de espera');
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_SERIAL);
            this.setTooltip('Serial.setTimeout(ms). Compatible con XML Botflow.');
        }
    };

    // BotFlow: serial_print — entrada CONTENT, sombra type "text"
    Blockly.Blocks['serial_print'] = {
        init: function() {
            this.appendValueInput('CONTENT')
                .setCheck(null)
                .appendField('Serial Print');
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_SERIAL);
            this.setTooltip('Serial.println(CONTENIDO). Compatible con XML Botflow.');
        }
    };

    // BotFlow: serial_disponible — Serial.available() > 0
    Blockly.Blocks['serial_disponible'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('Hay datos en el puerto serial');
            this.setOutput(true, 'Boolean');
            this.setColour(COLOUR_SERIAL);
            this.setTooltip('Serial.available() > 0. Compatible con XML Botflow.');
        }
    };

    // BotFlow: serial_read — Serial.readString()
    Blockly.Blocks['serial_read'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('Datos del puerto serial');
            this.setOutput(true, 'String');
            this.setColour(COLOUR_SERIAL);
            this.setTooltip('Serial.readString(). Compatible con XML Botflow.');
        }
    };

    // Número literal Blockly/Botflow (field NUM); mismo tipo que sombras en sumar, etc.
    if (typeof Blockly.Blocks['math_number'] === 'undefined') {
        Blockly.Blocks['math_number'] = {
            init: function() {
                this.appendDummyInput()
                    .appendField(new Blockly.FieldNumber(0), 'NUM');
                this.setOutput(true, 'Number');
                this.setColour(COLOUR_OPERATOR);
                this.setTooltip('Número (compat. importación Botflow / Blockly)');
            }
        };
    }

    // Texto literal Botflow / Blockly (categoría Texto; sombra en serial_print, etc.)
    if (typeof Blockly.Blocks['text'] === 'undefined') {
        Blockly.Blocks['text'] = {
            init: function() {
                this.appendDummyInput()
                    .appendField(new Blockly.FieldTextInput(''), 'TEXT');
                this.setOutput(true, 'String');
                this.setColour(COLOUR_TEXT);
                this.setTooltip('Texto literal (Botflow: text)');
            }
        };
    }

    // ============================================
    // calvin_ble_* - Bluetooth Low Energy (solo ESP32)
    // ============================================

    // 1) Inicializar BLE (BotFlow: ble_init - layout visual más parecido al original)
    Blockly.Blocks['calvin_ble_init'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Inicializar BLE");
            this.appendValueInput("NOMBRE")
                .setCheck("String")
                .appendField("Nombre");
            this.appendStatementInput("onConectado")
                .appendField("Conectado");
            this.appendStatementInput("onDesconectado")
                .appendField("Desconectado");
            this.appendStatementInput("SERVICES")
                .appendField("▸");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BLE);
            this.setTooltip("Inicializa BLE con nombre. Conectado/Desconectado: callbacks. Zona inferior: añade servicios BLE.");
        }
    };

    // 2) Servicio [NOMBRE] UUID [UUID] (BotFlow: ble_service)
    Blockly.Blocks['calvin_ble_service'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Servicio")
                .appendField(new Blockly.FieldTextInput("servicio"), "NOMBRE")
                .appendField("UUID")
                .appendField(new Blockly.FieldTextInput("4fafc201-1fb5-459e-8fcc-c5c9c331914b"), "UUID");
            this.appendStatementInput("CHARACTERISTICS")
                .appendField("Características");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BLE);
            this.setTooltip("Define un servicio BLE con UUID. Añade características dentro.");
        }
    };

    // 3) Caracteristica [NOMBRE] UUID [UUID] Hacer (BotFlow: ble_characteristic)
    Blockly.Blocks['calvin_ble_characteristic'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Caracteristica")
                .appendField(new Blockly.FieldTextInput("cmd"), "NOMBRE")
                .appendField("UUID")
                .appendField(new Blockly.FieldTextInput("beb5483e-36e1-4688-b7f5-ea07361b26a8"), "UUID");
            this.appendStatementInput("onWrite")
                .appendField("Hacer");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BLE);
            this.setTooltip("Define una característica BLE. El id se usa en BLE escribir.");
        }
    };

    // 4) ble_characteristic_write (BotFlow: ble write [SERVICIO] [CARACTERISTICA] to [VALUE])
    Blockly.Blocks['calvin_ble_write'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("ble write")
                .appendField(new Blockly.FieldDropdown([
                    ["Seleccione", "nothing_selected"],
                    ["servicio", "servicio"]
                ]), "SERVICIO")
                .appendField(new Blockly.FieldDropdown([
                    ["Seleccione", "nothing_selected"],
                    ["cmd", "cmd"]
                ]), "CARACTERISTICA");
            this.appendValueInput("VALUE")
                .setCheck(null)
                .appendField("to");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BLE);
            this.setTooltip("ble write [SERVICIO] [CARACTERISTICA] to [VALUE]. Solo ESP32.");
        }
    };

    // 5) ble_characteristic_value (BotFlow: Valor numérico de esta caracteristica)
    Blockly.Blocks['calvin_ble_char_value_number'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Valor numérico de esta caracteristica");
            this.setOutput(true, "Number");
            this.setColour(COLOUR_BLE);
            this.setTooltip("Valor numérico de la característica (contexto onWrite). Solo ESP32.");
        }
    };

    // 6) ble_characteristic_value_str (BotFlow: Valor string de esta caracteristica)
    Blockly.Blocks['calvin_ble_char_value_string'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Valor string de esta caracteristica");
            this.setOutput(true, "String");
            this.setColour(COLOUR_BLE);
            this.setTooltip("Valor string de la característica (contexto onWrite). Solo ESP32.");
        }
    };

    // ============================================
    // calvin_io_* - Entrada/Salida (IN/OUT)
    // ============================================

    // BotFlow: inout_highlow — campo BOOL HIGH/LOW (misma salida que calvin_io_high_low)
    Blockly.Blocks['inout_highlow'] = {
        init: function() {
            this.appendDummyInput()
                .appendField(new Blockly.FieldDropdown([['HIGH', 'HIGH'], ['LOW', 'LOW']]), 'BOOL');
            this.setOutput(true, 'Boolean');
            this.setColour(COLOUR_IO);
            this.setTooltip('HIGH o LOW (Botflow: inout_highlow)');
        }
    };

    // BotFlow: inout_digital_write — PIN y STAT como campos (sin value STAT)
    Blockly.Blocks['inout_digital_write'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('DigitalWrite PIN#')
                .appendField(new Blockly.FieldNumber(13, 0, 255), 'PIN')
                .appendField('Stat')
                .appendField(new Blockly.FieldDropdown([['HIGH', 'HIGH'], ['LOW', 'LOW']]), 'STAT');
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_IO);
            this.setTooltip('digitalWrite(pin, HIGH|LOW) (Botflow: inout_digital_write)');
        }
    };

    // BotFlow: inout_digital_read — «DigitalRead PIN#» + campo PIN
    Blockly.Blocks['inout_digital_read'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('DigitalRead PIN#')
                .appendField(new Blockly.FieldNumber(2, 0, 255), 'PIN');
            this.setOutput(true, 'Boolean');
            this.setColour(COLOUR_IO);
            this.setTooltip('digitalRead(pin) (Botflow: inout_digital_read)');
        }
    };

    // BotFlow: inout_analog_read — «AnalogRead PIN#» + PIN A0..A15 (valor literal p. ej. A0)
    Blockly.Blocks['inout_analog_read'] = {
        init: function() {
            var analogPinOptions = [];
            for (var i = 0; i <= 15; i++) {
                var ax = 'A' + i;
                analogPinOptions.push([ax, ax]);
            }
            this.appendDummyInput()
                .appendField('AnalogRead PIN#')
                .appendField(new Blockly.FieldDropdown(analogPinOptions), 'PIN');
            this.setOutput(true, 'Number');
            this.setColour(COLOUR_IO);
            this.setTooltip('analogRead(Ax) (Botflow: inout_analog_read)');
        }
    };

    // BotFlow: inout_analog_write — PIN + entrada NUM (valor PWM)
    Blockly.Blocks['inout_analog_write'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('AnalogWrite PIN#')
                .appendField(new Blockly.FieldNumber(9, 0, 255), 'PIN');
            this.appendValueInput('NUM')
                .setCheck(null);
            this.setInputsInline(true);
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_IO);
            this.setTooltip('analogWrite(pin, valor) (Botflow: inout_analog_write)');
        }
    };

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

    // Mutador igual que calvin_func_* pero cuerpo en STACK (Blockly/Botflow procedures_defnoreturn)
    const PROCEDURES_DEFNORETURN_MUTATOR = Object.assign({}, CALVIN_FUNC_MUTATOR, {
        updateShape_: function() {
            if (this.getInput('PARAMS_LABEL')) {
                this.removeInput('PARAMS_LABEL');
            }
            if (this.paramNames_.length > 0) {
                this.appendDummyInput('PARAMS_LABEL')
                    .appendField('with:')
                    .appendField(this.paramNames_.join(', '));
                this.moveInputBefore('PARAMS_LABEL', 'STACK');
            }
            if (this.getInput('STACK')) {
                this.getInput('STACK').setVisible(this.allowStatements_);
            }
        }
    });
    Blockly.Extensions.registerMutator('procedures_defnoreturn_mutator', PROCEDURES_DEFNORETURN_MUTATOR, calvinFuncMutatorHelper, ['calvin_func_mutatorarg']);

    // BotFlow / Blockly: procedures_defnoreturn — to [NAME] [PARAMS] + STACK (sombrero, sin prev/next)
    // Blockly 9+: la tuerca del mutador requiere `extensions`, no la propiedad .mutator.
    Blockly.Blocks['procedures_defnoreturn'] = {
        hasReturnType: false,
        extensions: ['procedures_defnoreturn_mutator'],
        init: function() {
            this.appendDummyInput()
                .appendField('to')
                .appendField(new Blockly.FieldTextInput('do something'), 'NAME')
                .appendField('', 'PARAMS');
            this.appendStatementInput('STACK');
            this.setColour(COLOUR_FUNC);
            this.setTooltip('Define una función sin retorno (Botflow / Blockly procedures_defnoreturn)');
            this.setPreviousStatement(false, null);
            this.setNextStatement(false, null);
        }
    };

    // BotFlow / Blockly: procedures_defreturn — to [NAME] [PARAMS] + STACK + return [RETURN]
    Blockly.Blocks['procedures_defreturn'] = {
        hasReturnType: true,
        extensions: ['procedures_defnoreturn_mutator'],
        init: function() {
            this.appendDummyInput()
                .appendField('to')
                .appendField(new Blockly.FieldTextInput('do something'), 'NAME')
                .appendField('', 'PARAMS');
            this.appendStatementInput('STACK');
            this.appendValueInput('RETURN')
                .setCheck(null)
                .appendField('return');
            this.setColour(COLOUR_FUNC);
            this.setTooltip('Define una función con valor de retorno (Botflow / Blockly procedures_defreturn)');
            this.setPreviousStatement(false, null);
            this.setNextStatement(false, null);
        }
    };

    // BotFlow / Blockly: procedures_ifreturn — sí [COND] return [VALUE]; mutation value 0 = sin expresión
    Blockly.Blocks['procedures_ifreturn'] = {
        hasReturnValue_: true,
        updateShape_: function() {
            if (this.getInput('VALUE')) {
                this.removeInput('VALUE');
            }
            if (this.hasReturnValue_) {
                this.appendValueInput('VALUE')
                    .setCheck(null)
                    .appendField('return');
            }
        },
        mutationToDom: function() {
            const container = Blockly.utils.xml.createElement('mutation');
            container.setAttribute('value', this.hasReturnValue_ ? '1' : '0');
            return container;
        },
        domToMutation: function(xmlElement) {
            this.hasReturnValue_ = xmlElement.getAttribute('value') !== '0';
            this.updateShape_();
        },
        init: function() {
            this.hasReturnValue_ = true;
            this.appendValueInput('CONDITION')
                .setCheck(null)
                .appendField('sí');
            this.updateShape_();
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_FUNC);
            this.setTooltip('Si la condición se cumple, return (Botflow / Blockly procedures_ifreturn)');
        }
    };

    // 1) Función sin retorno (void) - como original "to [do something]" con mutador
    Blockly.Blocks['calvin_func_defnoreturn'] = {
        hasReturnType: false,
        extensions: ['calvin_func_mutator'],
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

    // 2) Función con retorno - como original "to [do something2]" con return y mutador
    Blockly.Blocks['calvin_func_defreturn'] = {
        hasReturnType: true,
        extensions: ['calvin_func_mutator'],
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
        extensions: ['calvin_func_call_mutator'],
        init: function() {
            this.appendDummyInput()
                .appendField(new Blockly.FieldTextInput("do something"), "NAME");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_FUNC);
            this.setTooltip("Llama a una función. Usa la tuerca para añadir argumentos.");
        }
    };

    // Llamar función con retorno - con mutador para argumentos
    Blockly.Blocks['calvin_func_call_return'] = {
        extensions: ['calvin_func_call_mutator'],
        init: function() {
            this.appendDummyInput()
                .appendField(new Blockly.FieldTextInput("do something2"), "NAME");
            this.setOutput(true, null);
            this.setColour(COLOUR_FUNC);
            this.setTooltip("Llama a una función y usa el valor. Usa la tuerca para argumentos.");
        }
    };

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

    // 1) Inicializar sensor de proximidad (BotFlow: inicializar_sensor_distancia, sin fields)
    Blockly.Blocks['calvin_botflow1_init_proximidad'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Inicializar sensor de proximidad");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Inicializa el sensor de proximidad. Pines TRIG/ECHO desde calvin_hardware (ESP32: 18/36).");
        }
    };

    // 2) distancia [cm] (BotFlow: leer_sensor_distancia)
    Blockly.Blocks['calvin_botflow1_distancia'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("distancia [cm]");
            this.setOutput(true, "Number");
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Devuelve la distancia al obstáculo en centímetros");
        }
    };

    // 3) inicializar_notas (BotFlow: type inicializar_notas, sin fields, setup)
    Blockly.Blocks['calvin_botflow1_init_nota'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Inicializar Nota Musical");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Configura el buzzer para notas musicales. Pines desde calvin_hardware.");
        }
    };

    // 4) notas_musicales (BotFlow: type notas_musicales, fields nota, octava, durnota)
    Blockly.Blocks['calvin_botflow1_nota_octava'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Nota")
                .appendField(new Blockly.FieldDropdown([
                    ["Do", "NOTE_C"], ["Re", "NOTE_D"], ["Mi", "NOTE_E"], ["Fa", "NOTE_F"],
                    ["Sol", "NOTE_G"], ["La", "NOTE_A"], ["Si", "NOTE_B"]
                ]), "nota")
                .appendField("octava")
                .appendField(new Blockly.FieldNumber(0, 0, 5), "octava")
                .appendField("durante");
            this.appendDummyInput()
                .appendField(new Blockly.FieldDropdown([
                    ["0.5 seg", "0.5"], ["1 seg", "1"], ["2 seg", "2"], ["5 seg", "5"],
                    ["inf", "inf"]
                ]), "durnota")
                .appendField("seg");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Nota [nota] octava [octava] durante [durnota] seg. inf = hasta siguiente bloque");
        }
    };

    // 5) inicializar_led (BotFlow: type inicializar_led, field tipoLED)
    Blockly.Blocks['calvin_botflow1_init_rgb'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Inicializar led RGB tipo")
                .appendField(new Blockly.FieldDropdown([
                    ["A", "A"],
                    ["C", "C"]
                ]), "tipoLED");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Configura LED RGB tipo A (ánodo común) o C (cátodo común). Pines desde calvin_hardware.");
        }
    };

    // 6) led_RGB (BotFlow: type led_RGB, fields estado, color, durled)
    Blockly.Blocks['calvin_botflow1_led_color'] = {
        init: function() {
            this.appendDummyInput()
                .appendField(new Blockly.FieldDropdown([
                    ["Encender", "true"],
                    ["Apagar", "false"]
                ]), "estado")
                .appendField("led");
            this.appendDummyInput()
                .appendField(new Blockly.FieldDropdown([
                    ["Rojo", "rojo"],
                    ["Verde", "verde"],
                    ["Azul", "azul"],
                    ["Amarillo", "amarillo"],
                    ["Cyan", "cyan"],
                    ["Magenta", "magenta"],
                    ["Blanco", "blanco"]
                ]), "color");
            this.appendDummyInput()
                .appendField("durante")
                .appendField(new Blockly.FieldDropdown([
                    ["0.5 seg", "0.5"], ["1 seg", "1"], ["2 seg", "2"], ["5 seg", "5"],
                    ["inf", "inf"]
                ]), "durled")
                .appendField("seg");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("[estado] led [color] durante [durled] seg. inf = hasta siguiente bloque");
        }
    };

    // 7) Inicializar Motores (BotFlow: field pwmvalue; pines desde calvin_hardware)
    Blockly.Blocks['calvin_botflow1_init_motores'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Inicializar Motores")
                .appendField(new Blockly.FieldNumber(220, 0, 255), "pwmvalue")
                .appendField("PWM");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Configura motores del robot. PWM 0-255 (220 por defecto). Pines desde calvin_hardware.");
        }
    };

    // 8) ir [movimiento] durante [TIEMPO] seg (BotFlow: mover)
    Blockly.Blocks['calvin_botflow1_mover'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("ir")
                .appendField(new Blockly.FieldDropdown([
                    ["Adelante", "1"],
                    ["Atrás", "2"],
                    ["Izquierda", "3"],
                    ["Derecha", "4"]
                ]), "movimiento")
                .appendField("durante");
            this.appendValueInput("TIEMPO")
                .setCheck("Number")
                .appendField("");
            this.appendDummyInput().appendField("seg");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW1);
            this.setTooltip("Mueve el robot en la dirección indicada durante X segundos");
        }
    };

    // 9) Girar Motor [motor] en sentido [sentido] durante [TIEMPO] (BotFlow)
    Blockly.Blocks['calvin_botflow1_girar_motor'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Girar Motor")
                .appendField(new Blockly.FieldDropdown([
                    ["izquierdo", "0"],
                    ["derecho", "1"]
                ]), "motor")
                .appendField("en sentido")
                .appendField(new Blockly.FieldDropdown([
                    ["Horario", "1"],
                    ["Antihorario", "0"]
                ]), "sentido")
                .appendField("durante");
            this.appendValueInput("TIEMPO")
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

    // BotFlow: sensor/umbralSensor con values s_izquierdo, s_centro, s_derecho (mapeados a 0,1,2 en C)
    const SENSOR_LINEA_OPTIONS = [
        ["Izquierdo", "s_izquierdo"],
        ["Centro", "s_centro"],
        ["Derecho", "s_derecho"]
    ];

    // 1) Inicializar sensores de línea (BotFlow: inicializar_sensor_linea, sin fields)
    Blockly.Blocks['calvin_botflow2_init_lineas'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Inicializar sensores de línea");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW2);
            this.setTooltip("Configura los sensores de línea. Pines desde calvin_hardware (ESP32: 34,35,39).");
        }
    };

    // 2) Calibrar sensores de línea durante [ciclos] lecturas (BotFlow: calibrar_sensores_linea)
    Blockly.Blocks['calvin_botflow2_calibrar_lineas'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Calibrar sensores de línea durante")
                .appendField(new Blockly.FieldNumber(30, 1, 999), "ciclos")
                .appendField("lecturas");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(COLOUR_BOTFLOW2);
            this.setTooltip("Realiza n lecturas para calibrar min/max de cada sensor");
        }
    };

    // 3) Valor sensor de linea [sensor] (BotFlow: leer_sensores_linea)
    Blockly.Blocks['calvin_botflow2_linea_valor'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Valor sensor de linea")
                .appendField(new Blockly.FieldDropdown(SENSOR_LINEA_OPTIONS), "sensor");
            this.setOutput(true, "Number");
            this.setColour(COLOUR_BOTFLOW2);
            this.setTooltip("Devuelve el valor analógico (0-1023) del sensor");
        }
    };

    // 4) Valor umbral sensor de linea [sensor] (BotFlow: umbral_sensor)
    Blockly.Blocks['calvin_botflow2_linea_umbral'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Valor umbral sensor de linea")
                .appendField(new Blockly.FieldDropdown(SENSOR_LINEA_OPTIONS), "umbralSensor");
            this.setOutput(true, "Number");
            this.setColour(COLOUR_BOTFLOW2);
            this.setTooltip("Devuelve el umbral calibrado del sensor");
        }
    };

    // ============================================
    // BotFlow: contenedores setup / loop (XML import)
    // ============================================

    Blockly.Blocks['setup'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('Inicializar');
            this.appendStatementInput('setup');
            this.setColour(COLOUR_CONTROL);
            this.setTooltip('void setup() { … } (Botflow)');
            this.setDeletable(false);
            this.setMovable(false);
        }
    };

    Blockly.Blocks['loop'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('Bucle');
            this.appendStatementInput('loop');
            this.setColour(COLOUR_CONTROL);
            this.setTooltip('void loop() { … } (Botflow)');
            this.setDeletable(false);
            this.setMovable(false);
        }
    };

})();
