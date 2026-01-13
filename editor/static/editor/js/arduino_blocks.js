/**
 * Bloques personalizados de Arduino para Blockly
 */

// ============================================
// BLOQUES DE ESTRUCTURA PRINCIPAL
// ============================================

Blockly.Blocks['arduino_setup'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("⚙️ setup");
        this.appendStatementInput("SETUP_CODE")
            .setCheck(null);
        this.setColour(60);
        this.setTooltip("Código que se ejecuta una vez al iniciar");
        this.setHelpUrl("");
    }
};

Blockly.Blocks['arduino_loop'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("🔄 loop");
        this.appendStatementInput("LOOP_CODE")
            .setCheck(null);
        this.setColour(120);
        this.setTooltip("Código que se ejecuta continuamente");
        this.setHelpUrl("");
    }
};

// ============================================
// BLOQUES DE PINES DIGITALES
// ============================================

Blockly.Blocks['arduino_pin_mode'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("📌 pinMode pin")
            .appendField(new Blockly.FieldNumber(13, 0, 19), "PIN")
            .appendField("modo")
            .appendField(new Blockly.FieldDropdown([
                ["OUTPUT", "OUTPUT"],
                ["INPUT", "INPUT"],
                ["INPUT_PULLUP", "INPUT_PULLUP"]
            ]), "MODE");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(230);
        this.setTooltip("Configura un pin como entrada o salida");
    }
};

Blockly.Blocks['arduino_digital_write'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("💡 digitalWrite pin")
            .appendField(new Blockly.FieldNumber(13, 0, 19), "PIN")
            .appendField("valor")
            .appendField(new Blockly.FieldDropdown([
                ["HIGH", "HIGH"],
                ["LOW", "LOW"]
            ]), "VALUE");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(230);
        this.setTooltip("Escribe un valor digital en un pin");
    }
};

Blockly.Blocks['arduino_digital_read'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("📥 digitalRead pin")
            .appendField(new Blockly.FieldNumber(2, 0, 19), "PIN");
        this.setOutput(true, "Number");
        this.setColour(230);
        this.setTooltip("Lee el valor digital de un pin");
    }
};

// ============================================
// BLOQUES DE PINES ANALÓGICOS
// ============================================

Blockly.Blocks['arduino_analog_read'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("📊 analogRead pin A")
            .appendField(new Blockly.FieldNumber(0, 0, 5), "PIN");
        this.setOutput(true, "Number");
        this.setColour(180);
        this.setTooltip("Lee el valor analógico (0-1023) de un pin");
    }
};

Blockly.Blocks['arduino_analog_write'] = {
    init: function() {
        this.appendValueInput("VALUE")
            .setCheck("Number")
            .appendField("📈 analogWrite pin")
            .appendField(new Blockly.FieldNumber(9, 0, 13), "PIN")
            .appendField("valor");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(180);
        this.setTooltip("Escribe un valor PWM (0-255) en un pin");
    }
};

// ============================================
// BLOQUES DE TIEMPO
// ============================================

Blockly.Blocks['arduino_delay'] = {
    init: function() {
        this.appendValueInput("TIME")
            .setCheck("Number")
            .appendField("⏱️ esperar");
        this.appendDummyInput()
            .appendField("milisegundos");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(330);
        this.setTooltip("Pausa la ejecución por un tiempo");
    }
};

Blockly.Blocks['arduino_delay_microseconds'] = {
    init: function() {
        this.appendValueInput("TIME")
            .setCheck("Number")
            .appendField("⏱️ esperar");
        this.appendDummyInput()
            .appendField("microsegundos");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(330);
        this.setTooltip("Pausa la ejecución por microsegundos");
    }
};

Blockly.Blocks['arduino_millis'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("⏰ millis()");
        this.setOutput(true, "Number");
        this.setColour(330);
        this.setTooltip("Retorna el tiempo en milisegundos desde que inició el programa");
    }
};

Blockly.Blocks['arduino_micros'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("⏰ micros()");
        this.setOutput(true, "Number");
        this.setColour(330);
        this.setTooltip("Retorna el tiempo en microsegundos desde que inició el programa");
    }
};

// ============================================
// BLOQUES DE SERIAL
// ============================================

Blockly.Blocks['arduino_serial_begin'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("📡 Serial.begin")
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
        this.setColour(20);
        this.setTooltip("Inicia la comunicación serial");
    }
};

Blockly.Blocks['arduino_serial_print'] = {
    init: function() {
        this.appendValueInput("VALUE")
            .setCheck(null)
            .appendField("📝 Serial.print");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(20);
        this.setTooltip("Imprime un valor en el monitor serial");
    }
};

Blockly.Blocks['arduino_serial_println'] = {
    init: function() {
        this.appendValueInput("VALUE")
            .setCheck(null)
            .appendField("📝 Serial.println");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(20);
        this.setTooltip("Imprime un valor con salto de línea");
    }
};

Blockly.Blocks['arduino_serial_available'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("📨 Serial.available()");
        this.setOutput(true, "Number");
        this.setColour(20);
        this.setTooltip("Retorna el número de bytes disponibles para leer");
    }
};

Blockly.Blocks['arduino_serial_read'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("📖 Serial.read()");
        this.setOutput(true, "Number");
        this.setColour(20);
        this.setTooltip("Lee un byte del puerto serial");
    }
};

// ============================================
// BLOQUES DE VARIABLES
// ============================================

Blockly.Blocks['arduino_variable_int'] = {
    init: function() {
        this.appendValueInput("VALUE")
            .setCheck("Number")
            .appendField("int")
            .appendField(new Blockly.FieldTextInput("variable"), "NAME")
            .appendField("=");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(290);
        this.setTooltip("Declara una variable entera");
    }
};

Blockly.Blocks['arduino_variable_float'] = {
    init: function() {
        this.appendValueInput("VALUE")
            .setCheck("Number")
            .appendField("float")
            .appendField(new Blockly.FieldTextInput("variable"), "NAME")
            .appendField("=");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(290);
        this.setTooltip("Declara una variable decimal");
    }
};

Blockly.Blocks['arduino_variable_string'] = {
    init: function() {
        this.appendValueInput("VALUE")
            .setCheck("String")
            .appendField("String")
            .appendField(new Blockly.FieldTextInput("texto"), "NAME")
            .appendField("=");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(290);
        this.setTooltip("Declara una variable de texto");
    }
};

Blockly.Blocks['arduino_variable_boolean'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("bool")
            .appendField(new Blockly.FieldTextInput("flag"), "NAME")
            .appendField("=")
            .appendField(new Blockly.FieldDropdown([
                ["true", "true"],
                ["false", "false"]
            ]), "VALUE");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(290);
        this.setTooltip("Declara una variable booleana");
    }
};

Blockly.Blocks['arduino_get_variable'] = {
    init: function() {
        this.appendDummyInput()
            .appendField(new Blockly.FieldTextInput("variable"), "NAME");
        this.setOutput(true, null);
        this.setColour(290);
        this.setTooltip("Obtiene el valor de una variable");
    }
};

Blockly.Blocks['arduino_set_variable'] = {
    init: function() {
        this.appendValueInput("VALUE")
            .setCheck(null)
            .appendField(new Blockly.FieldTextInput("variable"), "NAME")
            .appendField("=");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(290);
        this.setTooltip("Asigna un valor a una variable");
    }
};

// ============================================
// BLOQUES DE MATEMÁTICAS
// ============================================

Blockly.Blocks['arduino_map'] = {
    init: function() {
        this.appendValueInput("VALUE")
            .setCheck("Number")
            .appendField("🔢 map");
        this.appendValueInput("FROM_LOW")
            .setCheck("Number")
            .appendField("de");
        this.appendValueInput("FROM_HIGH")
            .setCheck("Number")
            .appendField("-");
        this.appendValueInput("TO_LOW")
            .setCheck("Number")
            .appendField("a");
        this.appendValueInput("TO_HIGH")
            .setCheck("Number")
            .appendField("-");
        this.setInputsInline(true);
        this.setOutput(true, "Number");
        this.setColour(200);
        this.setTooltip("Mapea un valor de un rango a otro");
    }
};

Blockly.Blocks['arduino_constrain'] = {
    init: function() {
        this.appendValueInput("VALUE")
            .setCheck("Number")
            .appendField("🔒 constrain");
        this.appendValueInput("LOW")
            .setCheck("Number")
            .appendField("entre");
        this.appendValueInput("HIGH")
            .setCheck("Number")
            .appendField("y");
        this.setInputsInline(true);
        this.setOutput(true, "Number");
        this.setColour(200);
        this.setTooltip("Limita un valor entre un mínimo y máximo");
    }
};

Blockly.Blocks['arduino_random'] = {
    init: function() {
        this.appendValueInput("MIN")
            .setCheck("Number")
            .appendField("🎲 random de");
        this.appendValueInput("MAX")
            .setCheck("Number")
            .appendField("a");
        this.setInputsInline(true);
        this.setOutput(true, "Number");
        this.setColour(200);
        this.setTooltip("Genera un número aleatorio");
    }
};

// ============================================
// BLOQUES DE CONTROL
// ============================================

Blockly.Blocks['arduino_if'] = {
    init: function() {
        this.appendValueInput("CONDITION")
            .setCheck("Boolean")
            .appendField("🔀 si");
        this.appendStatementInput("DO")
            .setCheck(null)
            .appendField("entonces");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(210);
        this.setTooltip("Ejecuta código si la condición es verdadera");
    }
};

Blockly.Blocks['arduino_if_else'] = {
    init: function() {
        this.appendValueInput("CONDITION")
            .setCheck("Boolean")
            .appendField("🔀 si");
        this.appendStatementInput("DO")
            .setCheck(null)
            .appendField("entonces");
        this.appendStatementInput("ELSE")
            .setCheck(null)
            .appendField("sino");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(210);
        this.setTooltip("Ejecuta código si la condición es verdadera, sino ejecuta otro");
    }
};

Blockly.Blocks['arduino_for'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("🔁 repetir con")
            .appendField(new Blockly.FieldTextInput("i"), "VAR")
            .appendField("desde")
            .appendField(new Blockly.FieldNumber(0), "FROM")
            .appendField("hasta")
            .appendField(new Blockly.FieldNumber(10), "TO");
        this.appendStatementInput("DO")
            .setCheck(null);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(210);
        this.setTooltip("Repite el código un número de veces");
    }
};

Blockly.Blocks['arduino_while'] = {
    init: function() {
        this.appendValueInput("CONDITION")
            .setCheck("Boolean")
            .appendField("🔁 mientras");
        this.appendStatementInput("DO")
            .setCheck(null);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(210);
        this.setTooltip("Repite mientras la condición sea verdadera");
    }
};

// ============================================
// BLOQUES DE COMPARACIÓN
// ============================================

Blockly.Blocks['arduino_compare'] = {
    init: function() {
        this.appendValueInput("A")
            .setCheck("Number");
        this.appendDummyInput()
            .appendField(new Blockly.FieldDropdown([
                ["=", "=="],
                ["≠", "!="],
                ["<", "<"],
                ["≤", "<="],
                [">", ">"],
                ["≥", ">="]
            ]), "OP");
        this.appendValueInput("B")
            .setCheck("Number");
        this.setInputsInline(true);
        this.setOutput(true, "Boolean");
        this.setColour(210);
        this.setTooltip("Compara dos valores");
    }
};

Blockly.Blocks['arduino_logic'] = {
    init: function() {
        this.appendValueInput("A")
            .setCheck("Boolean");
        this.appendDummyInput()
            .appendField(new Blockly.FieldDropdown([
                ["y", "&&"],
                ["o", "||"]
            ]), "OP");
        this.appendValueInput("B")
            .setCheck("Boolean");
        this.setInputsInline(true);
        this.setOutput(true, "Boolean");
        this.setColour(210);
        this.setTooltip("Operación lógica");
    }
};

Blockly.Blocks['arduino_not'] = {
    init: function() {
        this.appendValueInput("VALUE")
            .setCheck("Boolean")
            .appendField("no");
        this.setOutput(true, "Boolean");
        this.setColour(210);
        this.setTooltip("Niega un valor booleano");
    }
};

Blockly.Blocks['arduino_true'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("verdadero");
        this.setOutput(true, "Boolean");
        this.setColour(210);
        this.setTooltip("Valor verdadero");
    }
};

Blockly.Blocks['arduino_false'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("falso");
        this.setOutput(true, "Boolean");
        this.setColour(210);
        this.setTooltip("Valor falso");
    }
};

// ============================================
// BLOQUES DE COMPONENTES COMUNES
// ============================================

Blockly.Blocks['arduino_led_builtin'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("💡 LED integrado")
            .appendField(new Blockly.FieldDropdown([
                ["encender", "HIGH"],
                ["apagar", "LOW"]
            ]), "STATE");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(40);
        this.setTooltip("Controla el LED integrado (pin 13)");
    }
};

Blockly.Blocks['arduino_tone'] = {
    init: function() {
        this.appendValueInput("FREQ")
            .setCheck("Number")
            .appendField("🔊 tone pin")
            .appendField(new Blockly.FieldNumber(8, 0, 13), "PIN")
            .appendField("frecuencia");
        this.appendValueInput("DURATION")
            .setCheck("Number")
            .appendField("duración");
        this.setInputsInline(true);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(40);
        this.setTooltip("Genera un tono en un buzzer");
    }
};

Blockly.Blocks['arduino_no_tone'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("🔇 noTone pin")
            .appendField(new Blockly.FieldNumber(8, 0, 13), "PIN");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(40);
        this.setTooltip("Detiene el tono");
    }
};

// ============================================
// BLOQUES DE SERVO (Servo.h)
// ============================================

Blockly.Blocks['arduino_servo_attach'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("🦾 servo")
            .appendField(new Blockly.FieldTextInput("servo1"), "NAME")
            .appendField("conectar pin")
            .appendField(new Blockly.FieldNumber(9, 0, 13), "PIN");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(270);
        this.setTooltip("Conecta un servo a un pin PWM");
    }
};

Blockly.Blocks['arduino_servo_attach_limits'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("🦾 servo")
            .appendField(new Blockly.FieldTextInput("servo1"), "NAME")
            .appendField("conectar pin")
            .appendField(new Blockly.FieldNumber(9, 0, 13), "PIN");
        this.appendDummyInput()
            .appendField("min µs")
            .appendField(new Blockly.FieldNumber(544, 0, 2500), "MIN")
            .appendField("max µs")
            .appendField(new Blockly.FieldNumber(2400, 500, 3000), "MAX");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(270);
        this.setTooltip("Conecta un servo con límites personalizados de pulso (microsegundos)");
    }
};

Blockly.Blocks['arduino_servo_write'] = {
    init: function() {
        this.appendValueInput("ANGLE")
            .setCheck("Number")
            .appendField("🦾 servo")
            .appendField(new Blockly.FieldTextInput("servo1"), "NAME")
            .appendField("mover a ángulo");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(270);
        this.setTooltip("Mueve el servo a un ángulo (0-180 grados)");
    }
};

Blockly.Blocks['arduino_servo_write_simple'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("🦾 servo")
            .appendField(new Blockly.FieldTextInput("servo1"), "NAME")
            .appendField(".write(")
            .appendField(new Blockly.FieldNumber(90, 0, 180), "ANGLE")
            .appendField("°)");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(270);
        this.setTooltip("Mueve el servo a un ángulo específico (0-180 grados)");
    }
};

Blockly.Blocks['arduino_servo_write_microseconds'] = {
    init: function() {
        this.appendValueInput("US")
            .setCheck("Number")
            .appendField("🦾 servo")
            .appendField(new Blockly.FieldTextInput("servo1"), "NAME")
            .appendField("mover a µs");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(270);
        this.setTooltip("Mueve el servo usando microsegundos (1000-2000 µs típico)");
    }
};

Blockly.Blocks['arduino_servo_read'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("🦾 servo")
            .appendField(new Blockly.FieldTextInput("servo1"), "NAME")
            .appendField("leer ángulo");
        this.setOutput(true, "Number");
        this.setColour(270);
        this.setTooltip("Lee el ángulo actual del servo (0-180)");
    }
};

Blockly.Blocks['arduino_servo_attached'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("🦾 servo")
            .appendField(new Blockly.FieldTextInput("servo1"), "NAME")
            .appendField("¿está conectado?");
        this.setOutput(true, "Boolean");
        this.setColour(270);
        this.setTooltip("Retorna verdadero si el servo está conectado a un pin");
    }
};

Blockly.Blocks['arduino_servo_detach'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("🦾 servo")
            .appendField(new Blockly.FieldTextInput("servo1"), "NAME")
            .appendField("desconectar");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(270);
        this.setTooltip("Desconecta el servo del pin (libera el pin para otros usos)");
    }
};

Blockly.Blocks['arduino_servo_sweep'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("🦾 servo")
            .appendField(new Blockly.FieldTextInput("servo1"), "NAME")
            .appendField("barrido de")
            .appendField(new Blockly.FieldNumber(0, 0, 180), "FROM")
            .appendField("a")
            .appendField(new Blockly.FieldNumber(180, 0, 180), "TO");
        this.appendValueInput("DELAY")
            .setCheck("Number")
            .appendField("retardo");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(270);
        this.setTooltip("Mueve el servo gradualmente de un ángulo a otro");
    }
};

// ============================================
// BLOQUES DE TEXTO/NÚMEROS
// ============================================

Blockly.Blocks['arduino_number'] = {
    init: function() {
        this.appendDummyInput()
            .appendField(new Blockly.FieldNumber(0), "NUM");
        this.setOutput(true, "Number");
        this.setColour(200);
        this.setTooltip("Un número");
    }
};

Blockly.Blocks['arduino_string'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('"')
            .appendField(new Blockly.FieldTextInput("texto"), "TEXT")
            .appendField('"');
        this.setOutput(true, "String");
        this.setColour(160);
        this.setTooltip("Un texto");
    }
};

Blockly.Blocks['arduino_math'] = {
    init: function() {
        this.appendValueInput("A")
            .setCheck("Number");
        this.appendDummyInput()
            .appendField(new Blockly.FieldDropdown([
                ["+", "+"],
                ["-", "-"],
                ["×", "*"],
                ["÷", "/"],
                ["%", "%"]
            ]), "OP");
        this.appendValueInput("B")
            .setCheck("Number");
        this.setInputsInline(true);
        this.setOutput(true, "Number");
        this.setColour(200);
        this.setTooltip("Operación matemática");
    }
};

// ============================================
// BLOQUE DE CÓDIGO PERSONALIZADO
// ============================================

Blockly.Blocks['arduino_custom_code'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("📝 código personalizado");
        this.appendDummyInput()
            .appendField(new Blockly.FieldMultilineInput("// tu código aquí"), "CODE");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(0);
        this.setTooltip("Inserta código Arduino personalizado");
    }
};

Blockly.Blocks['arduino_include'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("📚 #include <")
            .appendField(new Blockly.FieldTextInput("Servo.h"), "LIBRARY")
            .appendField(">");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(0);
        this.setTooltip("Incluye una librería");
    }
};

Blockly.Blocks['arduino_comment'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("💬")
            .appendField(new Blockly.FieldTextInput("comentario"), "COMMENT");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(0);
        this.setTooltip("Añade un comentario al código");
    }
};

