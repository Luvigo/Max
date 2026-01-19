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

// ============================================
// 🚗 GENERADORES DEL CARRITO MAX
// ============================================

// -------- INICIALIZACIÓN --------

arduinoGenerator.forBlock['max_init_motores'] = function(block) {
    const pinIzq = block.getFieldValue('PIN_IZQ');
    const pinDer = block.getFieldValue('PIN_DER');
    
    arduinoGenerator.includes_['servo'] = '#include <Servo.h>';
    arduinoGenerator.variables_['max_servos'] = `Servo servoIzq;\nServo servoDer;`;
    arduinoGenerator.variables_['max_config'] = `#define PIN_SERVO_IZQ ${pinIzq}\n#define PIN_SERVO_DER ${pinDer}\n#define STOP_IZQ 90\n#define STOP_DER 90`;
    
    // Agregar las funciones de movimiento
    arduinoGenerator.variables_['max_funciones'] = `
// Funciones de movimiento del carrito MAX
void adelante(int vel) {
  vel = constrain(vel, 0, 90);
  servoIzq.write(STOP_IZQ - vel);
  servoDer.write(STOP_DER + vel);
}

void atras(int vel) {
  vel = constrain(vel, 0, 90);
  servoIzq.write(STOP_IZQ + vel);
  servoDer.write(STOP_DER - vel);
}

void izquierda(int vel) {
  vel = constrain(vel, 0, 90);
  servoIzq.write(STOP_IZQ + vel);
  servoDer.write(STOP_DER + vel);
}

void derecha(int vel) {
  vel = constrain(vel, 0, 90);
  servoIzq.write(STOP_IZQ - vel);
  servoDer.write(STOP_DER - vel);
}

void detener() {
  servoIzq.write(STOP_IZQ);
  servoDer.write(STOP_DER);
}`;
    
    return `  servoIzq.attach(PIN_SERVO_IZQ);\n  servoDer.attach(PIN_SERVO_DER);\n  detener();\n`;
};

arduinoGenerator.forBlock['max_init_distancia'] = function(block) {
    const pinTrig = block.getFieldValue('PIN_TRIG');
    const pinEcho = block.getFieldValue('PIN_ECHO');
    
    arduinoGenerator.variables_['max_distancia_pins'] = `#define PIN_TRIG ${pinTrig}\n#define PIN_ECHO ${pinEcho}`;
    arduinoGenerator.variables_['max_distancia_vars'] = `long _max_duracion;\nfloat _max_distancia;`;
    
    // Función para medir distancia
    arduinoGenerator.variables_['max_distancia_func'] = `
// Función para medir distancia con sensor ultrasónico
float medirDistancia() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  _max_duracion = pulseIn(PIN_ECHO, HIGH, 30000);
  return _max_duracion * 0.034 / 2;
}`;
    
    return `  pinMode(PIN_TRIG, OUTPUT);\n  pinMode(PIN_ECHO, INPUT);\n`;
};

arduinoGenerator.forBlock['max_init_lineas'] = function(block) {
    const pinIzq = block.getFieldValue('PIN_IZQ');
    const pinCent = block.getFieldValue('PIN_CENT');
    const pinDer = block.getFieldValue('PIN_DER');
    
    arduinoGenerator.variables_['max_lineas_pins'] = `#define QTR_IZQ A${pinIzq}\n#define QTR_CENT A${pinCent}\n#define QTR_DER A${pinDer}`;
    
    return `  // Sensores de línea configurados en A${pinIzq}, A${pinCent}, A${pinDer}\n`;
};

arduinoGenerator.forBlock['max_init_buzzer'] = function(block) {
    const pin = block.getFieldValue('PIN');
    
    arduinoGenerator.variables_['max_buzzer_pin'] = `#define PIN_BUZZER ${pin}`;
    arduinoGenerator.variables_['max_notas'] = `// Notas musicales (Hz)\n#define NOTA_DO  262\n#define NOTA_RE  294\n#define NOTA_MI  330\n#define NOTA_FA  349\n#define NOTA_SOL 392\n#define NOTA_LA  440\n#define NOTA_SI  494`;
    
    // Función para tocar nota
    arduinoGenerator.variables_['max_buzzer_func'] = `
// Función para tocar una nota
void tocarNota(int frecuencia, int duracion) {
  tone(PIN_BUZZER, frecuencia, duracion);
  delay(duracion);
  noTone(PIN_BUZZER);
  delay(50);
}`;
    
    return `  pinMode(PIN_BUZZER, OUTPUT);\n`;
};

arduinoGenerator.forBlock['max_init_garra'] = function(block) {
    const pin = block.getFieldValue('PIN');
    const cerrada = block.getFieldValue('CERRADA');
    const abierta = block.getFieldValue('ABIERTA');
    
    arduinoGenerator.includes_['servo'] = '#include <Servo.h>';
    arduinoGenerator.variables_['max_garra'] = `Servo garra;\n#define PIN_GARRA ${pin}\n#define GARRA_CERRADA ${cerrada}\n#define GARRA_ABIERTA ${abierta}`;
    
    // Funciones de la garra
    arduinoGenerator.variables_['max_garra_func'] = `
// Funciones de la garra
void abrirGarra() {
  garra.write(GARRA_ABIERTA);
}

void cerrarGarra() {
  garra.write(GARRA_CERRADA);
}`;
    
    return `  garra.attach(PIN_GARRA);\n  cerrarGarra();\n`;
};

// -------- MOVIMIENTO DEL ROBOT --------

arduinoGenerator.forBlock['max_adelante'] = function(block) {
    const vel = block.getFieldValue('VEL');
    return `  adelante(${vel});\n`;
};

arduinoGenerator.forBlock['max_adelante_var'] = function(block) {
    const vel = arduinoGenerator.valueToCode(block, 'VEL', arduinoGenerator.ORDER_ATOMIC) || '30';
    return `  adelante(${vel});\n`;
};

arduinoGenerator.forBlock['max_atras'] = function(block) {
    const vel = block.getFieldValue('VEL');
    return `  atras(${vel});\n`;
};

arduinoGenerator.forBlock['max_atras_var'] = function(block) {
    const vel = arduinoGenerator.valueToCode(block, 'VEL', arduinoGenerator.ORDER_ATOMIC) || '30';
    return `  atras(${vel});\n`;
};

arduinoGenerator.forBlock['max_izquierda'] = function(block) {
    const vel = block.getFieldValue('VEL');
    return `  izquierda(${vel});\n`;
};

arduinoGenerator.forBlock['max_izquierda_var'] = function(block) {
    const vel = arduinoGenerator.valueToCode(block, 'VEL', arduinoGenerator.ORDER_ATOMIC) || '25';
    return `  izquierda(${vel});\n`;
};

arduinoGenerator.forBlock['max_derecha'] = function(block) {
    const vel = block.getFieldValue('VEL');
    return `  derecha(${vel});\n`;
};

arduinoGenerator.forBlock['max_derecha_var'] = function(block) {
    const vel = arduinoGenerator.valueToCode(block, 'VEL', arduinoGenerator.ORDER_ATOMIC) || '25';
    return `  derecha(${vel});\n`;
};

arduinoGenerator.forBlock['max_detener'] = function(block) {
    return `  detener();\n`;
};

// -------- SENSOR DE DISTANCIA --------

arduinoGenerator.forBlock['max_medir_distancia'] = function(block) {
    return ['medirDistancia()', arduinoGenerator.ORDER_ATOMIC];
};

arduinoGenerator.forBlock['max_distancia_menor_que'] = function(block) {
    const cm = block.getFieldValue('CM');
    return [`(medirDistancia() < ${cm})`, arduinoGenerator.ORDER_RELATIONAL];
};

arduinoGenerator.forBlock['max_distancia_mayor_que'] = function(block) {
    const cm = block.getFieldValue('CM');
    return [`(medirDistancia() > ${cm})`, arduinoGenerator.ORDER_RELATIONAL];
};

// -------- SENSOR DE LÍNEAS --------

arduinoGenerator.forBlock['max_leer_linea_izq'] = function(block) {
    return ['analogRead(QTR_IZQ)', arduinoGenerator.ORDER_ATOMIC];
};

arduinoGenerator.forBlock['max_leer_linea_centro'] = function(block) {
    return ['analogRead(QTR_CENT)', arduinoGenerator.ORDER_ATOMIC];
};

arduinoGenerator.forBlock['max_leer_linea_der'] = function(block) {
    return ['analogRead(QTR_DER)', arduinoGenerator.ORDER_ATOMIC];
};

arduinoGenerator.forBlock['max_linea_detectada'] = function(block) {
    const sensor = block.getFieldValue('SENSOR');
    const umbral = block.getFieldValue('UMBRAL');
    const sensorPin = sensor === 'IZQ' ? 'QTR_IZQ' : (sensor === 'CENT' ? 'QTR_CENT' : 'QTR_DER');
    return [`(analogRead(${sensorPin}) < ${umbral})`, arduinoGenerator.ORDER_RELATIONAL];
};

// -------- BUZZER / NOTAS MUSICALES --------

arduinoGenerator.forBlock['max_tocar_nota'] = function(block) {
    const nota = block.getFieldValue('NOTA');
    const duracion = block.getFieldValue('DURACION');
    return `  tocarNota(${nota}, ${duracion});\n`;
};

arduinoGenerator.forBlock['max_tocar_frecuencia'] = function(block) {
    const freq = arduinoGenerator.valueToCode(block, 'FREQ', arduinoGenerator.ORDER_ATOMIC) || '440';
    const duracion = arduinoGenerator.valueToCode(block, 'DURACION', arduinoGenerator.ORDER_ATOMIC) || '300';
    return `  tocarNota(${freq}, ${duracion});\n`;
};

arduinoGenerator.forBlock['max_detener_sonido'] = function(block) {
    return `  noTone(PIN_BUZZER);\n`;
};

arduinoGenerator.forBlock['max_beep'] = function(block) {
    return `  tocarNota(1000, 100);\n`;
};

// -------- GARRA --------

arduinoGenerator.forBlock['max_abrir_garra'] = function(block) {
    return `  abrirGarra();\n`;
};

arduinoGenerator.forBlock['max_cerrar_garra'] = function(block) {
    return `  cerrarGarra();\n`;
};

arduinoGenerator.forBlock['max_mover_garra'] = function(block) {
    const angulo = block.getFieldValue('ANGULO');
    return `  garra.write(${angulo});\n`;
};

// -------- COMBINACIONES ÚTILES --------

arduinoGenerator.forBlock['max_avanzar_tiempo'] = function(block) {
    const vel = block.getFieldValue('VEL');
    const tiempo = block.getFieldValue('TIEMPO');
    return `  adelante(${vel});\n  delay(${tiempo});\n  detener();\n`;
};

arduinoGenerator.forBlock['max_retroceder_tiempo'] = function(block) {
    const vel = block.getFieldValue('VEL');
    const tiempo = block.getFieldValue('TIEMPO');
    return `  atras(${vel});\n  delay(${tiempo});\n  detener();\n`;
};

arduinoGenerator.forBlock['max_girar_tiempo'] = function(block) {
    const dir = block.getFieldValue('DIR');
    const vel = block.getFieldValue('VEL');
    const tiempo = block.getFieldValue('TIEMPO');
    return `  ${dir}(${vel});\n  delay(${tiempo});\n  detener();\n`;
};

arduinoGenerator.forBlock['max_evitar_obstaculo'] = function(block) {
    const distancia = block.getFieldValue('DISTANCIA');
    const statements = arduinoGenerator.statementToCode(block, 'DO');
    return `  if (medirDistancia() < ${distancia}) {\n${statements}  }\n`;
};
