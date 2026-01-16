/**
 * Generador de código Arduino para Blockly
 */

// Crear el generador de Arduino
const arduinoGenerator = new Blockly.Generator('Arduino');

// Precedencia de operadores
arduinoGenerator.ORDER_ATOMIC = 0;
arduinoGenerator.ORDER_UNARY_POSTFIX = 1;
arduinoGenerator.ORDER_UNARY_PREFIX = 2;
arduinoGenerator.ORDER_MULTIPLICATIVE = 3;
arduinoGenerator.ORDER_ADDITIVE = 4;
arduinoGenerator.ORDER_SHIFT = 5;
arduinoGenerator.ORDER_RELATIONAL = 6;
arduinoGenerator.ORDER_EQUALITY = 7;
arduinoGenerator.ORDER_BITWISE_AND = 8;
arduinoGenerator.ORDER_BITWISE_XOR = 9;
arduinoGenerator.ORDER_BITWISE_OR = 10;
arduinoGenerator.ORDER_LOGICAL_AND = 11;
arduinoGenerator.ORDER_LOGICAL_OR = 12;
arduinoGenerator.ORDER_CONDITIONAL = 13;
arduinoGenerator.ORDER_ASSIGNMENT = 14;
arduinoGenerator.ORDER_NONE = 99;

// Variables para almacenar includes y variables globales
arduinoGenerator.includes_ = {};
arduinoGenerator.variables_ = {};
arduinoGenerator.setups_ = {};

// Función de inicialización
arduinoGenerator.init = function(workspace) {
    arduinoGenerator.includes_ = {};
    arduinoGenerator.variables_ = {};
    arduinoGenerator.setups_ = {};
};

// Función para terminar la generación
arduinoGenerator.finish = function(code) {
    // Generar includes
    let includes = '';
    for (let name in arduinoGenerator.includes_) {
        includes += arduinoGenerator.includes_[name] + '\n';
    }
    
    // Generar variables globales
    let variables = '';
    for (let name in arduinoGenerator.variables_) {
        variables += arduinoGenerator.variables_[name] + '\n';
    }
    
    // Generar setups adicionales
    let setups = '';
    for (let name in arduinoGenerator.setups_) {
        setups += '  ' + arduinoGenerator.setups_[name] + '\n';
    }
    
    let finalCode = '';
    if (includes) finalCode += includes + '\n';
    if (variables) finalCode += variables + '\n';
    finalCode += code;
    
    return finalCode;
};

// Función para añadir indentación
arduinoGenerator.scrubNakedValue = function(line) {
    return line + ';\n';
};

arduinoGenerator.scrub_ = function(block, code, opt_thisOnly) {
    const nextBlock = block.nextConnection && block.nextConnection.targetBlock();
    const nextCode = opt_thisOnly ? '' : arduinoGenerator.blockToCode(nextBlock);
    return code + nextCode;
};

// ============================================
// GENERADORES DE ESTRUCTURA PRINCIPAL
// ============================================

arduinoGenerator.forBlock['arduino_setup'] = function(block) {
    const statements = arduinoGenerator.statementToCode(block, 'SETUP_CODE');
    return 'void setup() {\n' + statements + '}\n\n';
};

arduinoGenerator.forBlock['arduino_loop'] = function(block) {
    const statements = arduinoGenerator.statementToCode(block, 'LOOP_CODE');
    return 'void loop() {\n' + statements + '}\n';
};

// ============================================
// GENERADORES DE PINES DIGITALES
// ============================================

arduinoGenerator.forBlock['arduino_pin_mode'] = function(block) {
    const pin = block.getFieldValue('PIN');
    const mode = block.getFieldValue('MODE');
    return `  pinMode(${pin}, ${mode});\n`;
};

arduinoGenerator.forBlock['arduino_digital_write'] = function(block) {
    const pin = block.getFieldValue('PIN');
    const value = block.getFieldValue('VALUE');
    return `  digitalWrite(${pin}, ${value});\n`;
};

arduinoGenerator.forBlock['arduino_digital_read'] = function(block) {
    const pin = block.getFieldValue('PIN');
    return [`digitalRead(${pin})`, arduinoGenerator.ORDER_ATOMIC];
};

// ============================================
// GENERADORES DE PINES ANALÓGICOS
// ============================================

arduinoGenerator.forBlock['arduino_analog_read'] = function(block) {
    const pin = block.getFieldValue('PIN');
    return [`analogRead(A${pin})`, arduinoGenerator.ORDER_ATOMIC];
};

arduinoGenerator.forBlock['arduino_analog_write'] = function(block) {
    const pin = block.getFieldValue('PIN');
    const value = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_ATOMIC) || '0';
    return `  analogWrite(${pin}, ${value});\n`;
};

// ============================================
// GENERADORES DE TIEMPO
// ============================================

arduinoGenerator.forBlock['arduino_delay'] = function(block) {
    const time = arduinoGenerator.valueToCode(block, 'TIME', arduinoGenerator.ORDER_ATOMIC) || '1000';
    return `  delay(${time});\n`;
};

arduinoGenerator.forBlock['arduino_delay_microseconds'] = function(block) {
    const time = arduinoGenerator.valueToCode(block, 'TIME', arduinoGenerator.ORDER_ATOMIC) || '1000';
    return `  delayMicroseconds(${time});\n`;
};

arduinoGenerator.forBlock['arduino_millis'] = function(block) {
    return ['millis()', arduinoGenerator.ORDER_ATOMIC];
};

arduinoGenerator.forBlock['arduino_micros'] = function(block) {
    return ['micros()', arduinoGenerator.ORDER_ATOMIC];
};

// ============================================
// GENERADORES DE SERIAL
// ============================================

arduinoGenerator.forBlock['arduino_serial_begin'] = function(block) {
    const baud = block.getFieldValue('BAUD');
    return `  Serial.begin(${baud});\n`;
};

arduinoGenerator.forBlock['arduino_serial_print'] = function(block) {
    const value = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_ATOMIC) || '""';
    return `  Serial.print(${value});\n`;
};

arduinoGenerator.forBlock['arduino_serial_println'] = function(block) {
    const value = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_ATOMIC) || '""';
    return `  Serial.println(${value});\n`;
};

arduinoGenerator.forBlock['arduino_serial_available'] = function(block) {
    return ['Serial.available()', arduinoGenerator.ORDER_ATOMIC];
};

arduinoGenerator.forBlock['arduino_serial_read'] = function(block) {
    return ['Serial.read()', arduinoGenerator.ORDER_ATOMIC];
};

// ============================================
// GENERADORES DE VARIABLES
// ============================================

arduinoGenerator.forBlock['arduino_variable_int'] = function(block) {
    const name = block.getFieldValue('NAME');
    const value = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_ATOMIC) || '0';
    return `  int ${name} = ${value};\n`;
};

arduinoGenerator.forBlock['arduino_variable_float'] = function(block) {
    const name = block.getFieldValue('NAME');
    const value = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_ATOMIC) || '0.0';
    return `  float ${name} = ${value};\n`;
};

arduinoGenerator.forBlock['arduino_variable_string'] = function(block) {
    const name = block.getFieldValue('NAME');
    const value = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_ATOMIC) || '""';
    return `  String ${name} = ${value};\n`;
};

arduinoGenerator.forBlock['arduino_variable_boolean'] = function(block) {
    const name = block.getFieldValue('NAME');
    const value = block.getFieldValue('VALUE');
    return `  bool ${name} = ${value};\n`;
};

arduinoGenerator.forBlock['arduino_get_variable'] = function(block) {
    const name = block.getFieldValue('NAME');
    return [name, arduinoGenerator.ORDER_ATOMIC];
};

arduinoGenerator.forBlock['arduino_set_variable'] = function(block) {
    const name = block.getFieldValue('NAME');
    const value = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_ATOMIC) || '0';
    return `  ${name} = ${value};\n`;
};

// ============================================
// GENERADORES DE MATEMÁTICAS
// ============================================

arduinoGenerator.forBlock['arduino_map'] = function(block) {
    const value = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_ATOMIC) || '0';
    const fromLow = arduinoGenerator.valueToCode(block, 'FROM_LOW', arduinoGenerator.ORDER_ATOMIC) || '0';
    const fromHigh = arduinoGenerator.valueToCode(block, 'FROM_HIGH', arduinoGenerator.ORDER_ATOMIC) || '1023';
    const toLow = arduinoGenerator.valueToCode(block, 'TO_LOW', arduinoGenerator.ORDER_ATOMIC) || '0';
    const toHigh = arduinoGenerator.valueToCode(block, 'TO_HIGH', arduinoGenerator.ORDER_ATOMIC) || '255';
    return [`map(${value}, ${fromLow}, ${fromHigh}, ${toLow}, ${toHigh})`, arduinoGenerator.ORDER_ATOMIC];
};

arduinoGenerator.forBlock['arduino_constrain'] = function(block) {
    const value = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_ATOMIC) || '0';
    const low = arduinoGenerator.valueToCode(block, 'LOW', arduinoGenerator.ORDER_ATOMIC) || '0';
    const high = arduinoGenerator.valueToCode(block, 'HIGH', arduinoGenerator.ORDER_ATOMIC) || '255';
    return [`constrain(${value}, ${low}, ${high})`, arduinoGenerator.ORDER_ATOMIC];
};

arduinoGenerator.forBlock['arduino_random'] = function(block) {
    const min = arduinoGenerator.valueToCode(block, 'MIN', arduinoGenerator.ORDER_ATOMIC) || '0';
    const max = arduinoGenerator.valueToCode(block, 'MAX', arduinoGenerator.ORDER_ATOMIC) || '100';
    return [`random(${min}, ${max})`, arduinoGenerator.ORDER_ATOMIC];
};

// ============================================
// GENERADORES DE CONTROL
// ============================================

arduinoGenerator.forBlock['arduino_if'] = function(block) {
    const condition = arduinoGenerator.valueToCode(block, 'CONDITION', arduinoGenerator.ORDER_ATOMIC) || 'false';
    const statements = arduinoGenerator.statementToCode(block, 'DO');
    return `  if (${condition}) {\n${statements}  }\n`;
};

arduinoGenerator.forBlock['arduino_if_else'] = function(block) {
    const condition = arduinoGenerator.valueToCode(block, 'CONDITION', arduinoGenerator.ORDER_ATOMIC) || 'false';
    const doStatements = arduinoGenerator.statementToCode(block, 'DO');
    const elseStatements = arduinoGenerator.statementToCode(block, 'ELSE');
    return `  if (${condition}) {\n${doStatements}  } else {\n${elseStatements}  }\n`;
};

arduinoGenerator.forBlock['arduino_for'] = function(block) {
    const variable = block.getFieldValue('VAR');
    const from = block.getFieldValue('FROM');
    const to = block.getFieldValue('TO');
    const statements = arduinoGenerator.statementToCode(block, 'DO');
    return `  for (int ${variable} = ${from}; ${variable} <= ${to}; ${variable}++) {\n${statements}  }\n`;
};

arduinoGenerator.forBlock['arduino_while'] = function(block) {
    const condition = arduinoGenerator.valueToCode(block, 'CONDITION', arduinoGenerator.ORDER_ATOMIC) || 'false';
    const statements = arduinoGenerator.statementToCode(block, 'DO');
    return `  while (${condition}) {\n${statements}  }\n`;
};

// ============================================
// GENERADORES DE COMPARACIÓN
// ============================================

arduinoGenerator.forBlock['arduino_compare'] = function(block) {
    const a = arduinoGenerator.valueToCode(block, 'A', arduinoGenerator.ORDER_ATOMIC) || '0';
    const op = block.getFieldValue('OP');
    const b = arduinoGenerator.valueToCode(block, 'B', arduinoGenerator.ORDER_ATOMIC) || '0';
    return [`(${a} ${op} ${b})`, arduinoGenerator.ORDER_RELATIONAL];
};

arduinoGenerator.forBlock['arduino_logic'] = function(block) {
    const a = arduinoGenerator.valueToCode(block, 'A', arduinoGenerator.ORDER_ATOMIC) || 'false';
    const op = block.getFieldValue('OP');
    const b = arduinoGenerator.valueToCode(block, 'B', arduinoGenerator.ORDER_ATOMIC) || 'false';
    return [`(${a} ${op} ${b})`, arduinoGenerator.ORDER_LOGICAL_AND];
};

arduinoGenerator.forBlock['arduino_not'] = function(block) {
    const value = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_ATOMIC) || 'false';
    return [`!${value}`, arduinoGenerator.ORDER_UNARY_PREFIX];
};

arduinoGenerator.forBlock['arduino_true'] = function(block) {
    return ['true', arduinoGenerator.ORDER_ATOMIC];
};

arduinoGenerator.forBlock['arduino_false'] = function(block) {
    return ['false', arduinoGenerator.ORDER_ATOMIC];
};

// ============================================
// GENERADORES DE COMPONENTES
// ============================================

arduinoGenerator.forBlock['arduino_led_builtin'] = function(block) {
    const state = block.getFieldValue('STATE');
    arduinoGenerator.setups_['led_builtin'] = 'pinMode(LED_BUILTIN, OUTPUT);';
    return `  digitalWrite(LED_BUILTIN, ${state});\n`;
};

arduinoGenerator.forBlock['arduino_tone'] = function(block) {
    const pin = block.getFieldValue('PIN');
    const freq = arduinoGenerator.valueToCode(block, 'FREQ', arduinoGenerator.ORDER_ATOMIC) || '440';
    const duration = arduinoGenerator.valueToCode(block, 'DURATION', arduinoGenerator.ORDER_ATOMIC) || '500';
    return `  tone(${pin}, ${freq}, ${duration});\n`;
};

arduinoGenerator.forBlock['arduino_no_tone'] = function(block) {
    const pin = block.getFieldValue('PIN');
    return `  noTone(${pin});\n`;
};

// ============================================
// GENERADORES DE SERVO (Servo.h)
// ============================================

arduinoGenerator.forBlock['arduino_servo_attach'] = function(block) {
    const name = block.getFieldValue('NAME');
    const pin = block.getFieldValue('PIN');
    arduinoGenerator.includes_['servo'] = '#include <Servo.h>';
    arduinoGenerator.variables_[name] = `Servo ${name};`;
    return `  ${name}.attach(${pin});\n`;
};

arduinoGenerator.forBlock['arduino_servo_attach_limits'] = function(block) {
    const name = block.getFieldValue('NAME');
    const pin = block.getFieldValue('PIN');
    const min = block.getFieldValue('MIN');
    const max = block.getFieldValue('MAX');
    arduinoGenerator.includes_['servo'] = '#include <Servo.h>';
    arduinoGenerator.variables_[name] = `Servo ${name};`;
    return `  ${name}.attach(${pin}, ${min}, ${max});\n`;
};

arduinoGenerator.forBlock['arduino_servo_write'] = function(block) {
    const name = block.getFieldValue('NAME');
    const angle = arduinoGenerator.valueToCode(block, 'ANGLE', arduinoGenerator.ORDER_ATOMIC) || '90';
    return `  ${name}.write(${angle});\n`;
};

arduinoGenerator.forBlock['arduino_servo_write_simple'] = function(block) {
    const name = block.getFieldValue('NAME');
    const angle = block.getFieldValue('ANGLE');
    return `  ${name}.write(${angle});\n`;
};

arduinoGenerator.forBlock['arduino_servo_write_microseconds'] = function(block) {
    const name = block.getFieldValue('NAME');
    const us = arduinoGenerator.valueToCode(block, 'US', arduinoGenerator.ORDER_ATOMIC) || '1500';
    return `  ${name}.writeMicroseconds(${us});\n`;
};

arduinoGenerator.forBlock['arduino_servo_read'] = function(block) {
    const name = block.getFieldValue('NAME');
    return [`${name}.read()`, arduinoGenerator.ORDER_ATOMIC];
};

arduinoGenerator.forBlock['arduino_servo_attached'] = function(block) {
    const name = block.getFieldValue('NAME');
    return [`${name}.attached()`, arduinoGenerator.ORDER_ATOMIC];
};

arduinoGenerator.forBlock['arduino_servo_detach'] = function(block) {
    const name = block.getFieldValue('NAME');
    return `  ${name}.detach();\n`;
};

arduinoGenerator.forBlock['arduino_servo_sweep'] = function(block) {
    const name = block.getFieldValue('NAME');
    const from = block.getFieldValue('FROM');
    const to = block.getFieldValue('TO');
    const delay = arduinoGenerator.valueToCode(block, 'DELAY', arduinoGenerator.ORDER_ATOMIC) || '15';
    
    // Generar código de barrido
    let code = '';
    if (from <= to) {
        code = `  for (int pos = ${from}; pos <= ${to}; pos++) {\n`;
        code += `    ${name}.write(pos);\n`;
        code += `    delay(${delay});\n`;
        code += `  }\n`;
    } else {
        code = `  for (int pos = ${from}; pos >= ${to}; pos--) {\n`;
        code += `    ${name}.write(pos);\n`;
        code += `    delay(${delay});\n`;
        code += `  }\n`;
    }
    return code;
};

// ============================================
// GENERADORES DE TEXTO/NÚMEROS
// ============================================

arduinoGenerator.forBlock['arduino_number'] = function(block) {
    const num = block.getFieldValue('NUM');
    return [String(num), arduinoGenerator.ORDER_ATOMIC];
};

arduinoGenerator.forBlock['arduino_string'] = function(block) {
    const text = block.getFieldValue('TEXT');
    return [`"${text}"`, arduinoGenerator.ORDER_ATOMIC];
};

arduinoGenerator.forBlock['arduino_math'] = function(block) {
    const a = arduinoGenerator.valueToCode(block, 'A', arduinoGenerator.ORDER_ATOMIC) || '0';
    const op = block.getFieldValue('OP');
    const b = arduinoGenerator.valueToCode(block, 'B', arduinoGenerator.ORDER_ATOMIC) || '0';
    const order = (op === '+' || op === '-') ? arduinoGenerator.ORDER_ADDITIVE : arduinoGenerator.ORDER_MULTIPLICATIVE;
    return [`(${a} ${op} ${b})`, order];
};

// ============================================
// GENERADORES DE CÓDIGO PERSONALIZADO
// ============================================

arduinoGenerator.forBlock['arduino_custom_code'] = function(block) {
    const code = block.getFieldValue('CODE');
    return `  ${code}\n`;
};

arduinoGenerator.forBlock['arduino_include'] = function(block) {
    const library = block.getFieldValue('LIBRARY');
    arduinoGenerator.includes_[library] = `#include <${library}>`;
    return '';
};

arduinoGenerator.forBlock['arduino_comment'] = function(block) {
    const comment = block.getFieldValue('COMMENT');
    return `  // ${comment}\n`;
};

