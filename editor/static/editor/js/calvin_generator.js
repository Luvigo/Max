/**
 * Calvin - Generador de código
 * Usa arduinoGenerator (includes_, variables_, setups_)
 * No modifica max_* ni arduino_*
 */

(function() {
    'use strict';

    if (typeof arduinoGenerator === 'undefined') return;

    // ============================================
    // calvin_control_*
    // ============================================

    // 1) Esperar [n] ms -> delay(ms)
    arduinoGenerator.forBlock['calvin_control_delay'] = function(block) {
        const ms = arduinoGenerator.valueToCode(block, 'MS', arduinoGenerator.ORDER_ATOMIC) || '0';
        return `  delay(${ms});\n`;
    };

    // 2) En caso de que [valor] -> switch/case
    arduinoGenerator.forBlock['calvin_control_switch'] = function(block) {
        const value = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_ATOMIC) || '0';
        let casesCode = '';
        let child = block.getInputTargetBlock('CASES');
        while (child) {
            if (child.type === 'calvin_control_case') {
                const caseVal = arduinoGenerator.valueToCode(child, 'VALUE', arduinoGenerator.ORDER_ATOMIC) || '0';
                const doCode = arduinoGenerator.statementToCode(child, 'DO') || '';
                const indent = doCode ? '  ' + doCode.replace(/\n/g, '\n  ') + '\n' : '';
                casesCode += `    case ${caseVal}:\n${indent}    break;\n`;
            } else if (child.type === 'calvin_control_default') {
                const doCode = arduinoGenerator.statementToCode(child, 'DO') || '';
                casesCode += `    default:\n${doCode ? '  ' + doCode.replace(/\n/g, '\n  ') : ''}\n`;
            }
            child = child.getNextBlock();
        }
        return `  switch (${value}) {\n${casesCode}  }\n`;
    };

    // 3) Sea [valor] Hacer ... (generado por switch)
    arduinoGenerator.forBlock['calvin_control_case'] = function(block) {
        return '';
    };

    // 4) Si nada se cumplió (generado por switch)
    arduinoGenerator.forBlock['calvin_control_default'] = function(block) {
        return '';
    };

    // 5) repetir mientras -> while
    arduinoGenerator.forBlock['calvin_control_while'] = function(block) {
        const cond = arduinoGenerator.valueToCode(block, 'CONDITION', arduinoGenerator.ORDER_ATOMIC) || 'false';
        const statements = arduinoGenerator.statementToCode(block, 'DO');
        return `  while (${cond}) {\n${statements}  }\n`;
    };

    // 6) contar [i] de [inicio] a [fin] añadiendo [paso] -> for
    arduinoGenerator.forBlock['calvin_control_for'] = function(block) {
        const variable = block.getFieldValue('VAR') || 'i';
        const from = arduinoGenerator.valueToCode(block, 'FROM', arduinoGenerator.ORDER_ATOMIC) || '0';
        const to = arduinoGenerator.valueToCode(block, 'TO', arduinoGenerator.ORDER_ATOMIC) || '10';
        const step = arduinoGenerator.valueToCode(block, 'STEP', arduinoGenerator.ORDER_ATOMIC) || '1';
        const statements = arduinoGenerator.statementToCode(block, 'DO');
        return `  for (int ${variable} = ${from}; ${variable} <= ${to}; ${variable} += ${step}) {\n${statements}  }\n`;
    };

    // 7) si [condición] entonces -> if
    arduinoGenerator.forBlock['calvin_control_if'] = function(block) {
        const cond = arduinoGenerator.valueToCode(block, 'CONDITION', arduinoGenerator.ORDER_ATOMIC) || 'false';
        const statements = arduinoGenerator.statementToCode(block, 'DO');
        return `  if (${cond}) {\n${statements}  }\n`;
    };

    // 8) si [condición] entonces ... si no ... -> if/else
    arduinoGenerator.forBlock['calvin_control_if_else'] = function(block) {
        const cond = arduinoGenerator.valueToCode(block, 'CONDITION', arduinoGenerator.ORDER_ATOMIC) || 'false';
        const doStatements = arduinoGenerator.statementToCode(block, 'DO');
        const elseStatements = arduinoGenerator.statementToCode(block, 'ELSE');
        return `  if (${cond}) {\n${doStatements}  } else {\n${elseStatements}  }\n`;
    };

    // ============================================
    // calvin_operator_*
    // ============================================

    // número literal
    arduinoGenerator.forBlock['calvin_operator_number'] = function(block) {
        const num = block.getFieldValue('NUM');
        return [String(num), arduinoGenerator.ORDER_ATOMIC];
    };

    // suma
    arduinoGenerator.forBlock['calvin_operator_add'] = function(block) {
        const a = arduinoGenerator.valueToCode(block, 'A', arduinoGenerator.ORDER_ADDITION) || '0';
        const b = arduinoGenerator.valueToCode(block, 'B', arduinoGenerator.ORDER_ADDITION) || '0';
        return [`(${a} + ${b})`, arduinoGenerator.ORDER_ADDITION];
    };

    // resta
    arduinoGenerator.forBlock['calvin_operator_subtract'] = function(block) {
        const a = arduinoGenerator.valueToCode(block, 'A', arduinoGenerator.ORDER_ADDITION) || '0';
        const b = arduinoGenerator.valueToCode(block, 'B', arduinoGenerator.ORDER_ADDITION) || '0';
        return [`(${a} - ${b})`, arduinoGenerator.ORDER_ADDITION];
    };

    // multiplicación
    arduinoGenerator.forBlock['calvin_operator_multiply'] = function(block) {
        const a = arduinoGenerator.valueToCode(block, 'A', arduinoGenerator.ORDER_MULTIPLICATIVE) || '0';
        const b = arduinoGenerator.valueToCode(block, 'B', arduinoGenerator.ORDER_MULTIPLICATIVE) || '0';
        return [`(${a} * ${b})`, arduinoGenerator.ORDER_MULTIPLICATIVE];
    };

    // división
    arduinoGenerator.forBlock['calvin_operator_divide'] = function(block) {
        const a = arduinoGenerator.valueToCode(block, 'A', arduinoGenerator.ORDER_MULTIPLICATIVE) || '0';
        const b = arduinoGenerator.valueToCode(block, 'B', arduinoGenerator.ORDER_MULTIPLICATIVE) || '1';
        return [`(${a} / ${b})`, arduinoGenerator.ORDER_MULTIPLICATIVE];
    };

    // número aleatorio entre X y Y (inclusivo)
    arduinoGenerator.forBlock['calvin_operator_random'] = function(block) {
        const min = arduinoGenerator.valueToCode(block, 'MIN', arduinoGenerator.ORDER_ATOMIC) || '0';
        const max = arduinoGenerator.valueToCode(block, 'MAX', arduinoGenerator.ORDER_ATOMIC) || '100';
        return [`random(${min}, (${max}) + 1)`, arduinoGenerator.ORDER_ATOMIC];
    };

    // >, <, =
    arduinoGenerator.forBlock['calvin_operator_gt'] = function(block) {
        const a = arduinoGenerator.valueToCode(block, 'A', arduinoGenerator.ORDER_RELATIONAL) || '0';
        const b = arduinoGenerator.valueToCode(block, 'B', arduinoGenerator.ORDER_RELATIONAL) || '0';
        return [`(${a} > ${b})`, arduinoGenerator.ORDER_RELATIONAL];
    };

    arduinoGenerator.forBlock['calvin_operator_lt'] = function(block) {
        const a = arduinoGenerator.valueToCode(block, 'A', arduinoGenerator.ORDER_RELATIONAL) || '0';
        const b = arduinoGenerator.valueToCode(block, 'B', arduinoGenerator.ORDER_RELATIONAL) || '0';
        return [`(${a} < ${b})`, arduinoGenerator.ORDER_RELATIONAL];
    };

    arduinoGenerator.forBlock['calvin_operator_eq'] = function(block) {
        const a = arduinoGenerator.valueToCode(block, 'A', arduinoGenerator.ORDER_EQUALITY) || '0';
        const b = arduinoGenerator.valueToCode(block, 'B', arduinoGenerator.ORDER_EQUALITY) || '0';
        return [`(${a} == ${b})`, arduinoGenerator.ORDER_EQUALITY];
    };

    // y, o
    arduinoGenerator.forBlock['calvin_operator_and'] = function(block) {
        const a = arduinoGenerator.valueToCode(block, 'A', arduinoGenerator.ORDER_LOGICAL_AND) || 'false';
        const b = arduinoGenerator.valueToCode(block, 'B', arduinoGenerator.ORDER_LOGICAL_AND) || 'false';
        return [`(${a} && ${b})`, arduinoGenerator.ORDER_LOGICAL_AND];
    };

    arduinoGenerator.forBlock['calvin_operator_or'] = function(block) {
        const a = arduinoGenerator.valueToCode(block, 'A', arduinoGenerator.ORDER_LOGICAL_OR) || 'false';
        const b = arduinoGenerator.valueToCode(block, 'B', arduinoGenerator.ORDER_LOGICAL_OR) || 'false';
        return [`(${a} || ${b})`, arduinoGenerator.ORDER_LOGICAL_OR];
    };

    // raíz cuadrada - requiere math.h
    arduinoGenerator.forBlock['calvin_operator_sqrt'] = function(block) {
        const x = arduinoGenerator.valueToCode(block, 'X', arduinoGenerator.ORDER_NONE) || '0';
        if (!arduinoGenerator.includes_['math']) {
            arduinoGenerator.includes_['math'] = '#include <math.h>';
        }
        return [`sqrt(${x})`, arduinoGenerator.ORDER_ATOMIC];
    };

    // compare (general)
    arduinoGenerator.forBlock['calvin_operator_compare'] = function(block) {
        const a = arduinoGenerator.valueToCode(block, 'A', arduinoGenerator.ORDER_RELATIONAL) || '0';
        const b = arduinoGenerator.valueToCode(block, 'B', arduinoGenerator.ORDER_RELATIONAL) || '0';
        const op = block.getFieldValue('OP');
        const ops = { EQ: '==', NEQ: '!=', LT: '<', LTE: '<=', GT: '>', GTE: '>=' };
        return [`(${a} ${ops[op] || '=='} ${b})`, arduinoGenerator.ORDER_RELATIONAL];
    };

    // ============================================
    // calvin_text_*
    // ============================================

    // texto literal
    arduinoGenerator.forBlock['calvin_text_string'] = function(block) {
        const text = block.getFieldValue('TEXT') || '';
        const escaped = String(text).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
        return [`"${escaped}"`, arduinoGenerator.ORDER_ATOMIC];
    };

    arduinoGenerator.forBlock['calvin_text_concat'] = function(block) {
        const a = arduinoGenerator.valueToCode(block, 'A', arduinoGenerator.ORDER_ADDITION) || '""';
        const b = arduinoGenerator.valueToCode(block, 'B', arduinoGenerator.ORDER_ADDITION) || '""';
        return [`(String)(${a}) + (String)(${b})`, arduinoGenerator.ORDER_ADDITION];
    };

    // ============================================
    // calvin_serial_*
    // ============================================

    // 1) Inicializar Serial [baud] -> Serial.begin(baud)
    arduinoGenerator.forBlock['calvin_serial_begin'] = function(block) {
        const baud = block.getFieldValue('BAUD') || '9600';
        return `  Serial.begin(${baud});\n`;
    };

    // 2) Serial tiempo de espera [n] -> Serial.setTimeout(ms)
    arduinoGenerator.forBlock['calvin_serial_set_timeout'] = function(block) {
        const ms = arduinoGenerator.valueToCode(block, 'MS', arduinoGenerator.ORDER_ATOMIC) || '1000';
        return `  Serial.setTimeout(${ms});\n`;
    };

    // 3) Serial Print [valor] -> Serial.println para salida legible
    arduinoGenerator.forBlock['calvin_serial_print'] = function(block) {
        const val = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_NONE) || '""';
        return `  Serial.println(${val});\n`;
    };

    // 4) Hay datos en el puerto serial -> (Serial.available() > 0)
    arduinoGenerator.forBlock['calvin_serial_has_data'] = function(block) {
        return ['(Serial.available() > 0)', arduinoGenerator.ORDER_RELATIONAL];
    };

    // 5) Datos del puerto serial -> Serial.readString()
    arduinoGenerator.forBlock['calvin_serial_read_string'] = function(block) {
        return ['Serial.readString()', arduinoGenerator.ORDER_ATOMIC];
    };

    // ============================================
    // calvin_ble_* - Solo ESP32; AVR: comentarios/warning
    // ============================================

    function isBleEsp32() {
        try {
            if (typeof getBoardFamily === 'function' && typeof currentBoard !== 'undefined') {
                return getBoardFamily(currentBoard) === 'esp32';
            }
        } catch (e) { /* ignore */ }
        return false;
    }

    function sanitizeBleName(name) {
        return String(name || 'cmd').replace(/[^a-zA-Z0-9_]/g, '_').replace(/^_+|_+$/g, '') || 'cmd';
    }

    // 1) Inicializar BLE
    arduinoGenerator.forBlock['calvin_ble_init'] = function(block) {
        const name = block.getFieldValue('NAME') || 'CalvinBot';
        const nameEsc = String(name).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
        if (!isBleEsp32()) {
            return `  // BLE: Solo compatible con ESP32. Placa actual no soporta BLE.\n`;
        }
        if (!arduinoGenerator.includes_['ble']) {
            arduinoGenerator.includes_['ble'] = '#include <BLEDevice.h>\n#include <BLEServer.h>\n#include <BLEUtils.h>\n#include <BLE2902.h>';
        }
        if (!arduinoGenerator.variables_['ble_globals']) {
            arduinoGenerator.variables_['ble_globals'] =
                'BLEServer *pServer = nullptr;\nString _ble_last_value;';
        }
        const connectedCode = (arduinoGenerator.statementToCode(block, 'CONNECTED') || '').trim();
        const disconnectedCode = (arduinoGenerator.statementToCode(block, 'DISCONNECTED') || '').trim();
        const connBody = connectedCode ? '\n  ' + connectedCode.replace(/\n/g, '\n  ') : '';
        const discBody = disconnectedCode ? '\n  ' + disconnectedCode.replace(/\n/g, '\n  ') : '';
        if (!arduinoGenerator.variables_['ble_server_callbacks']) {
            arduinoGenerator.variables_['ble_server_callbacks'] =
                'class BLE_ServerCallbacks : public BLEServerCallbacks {\n' +
                '  void onConnect(BLEServer* p) {(void)p;' + connBody + '}\n' +
                '  void onDisconnect(BLEServer* p) {(void)p;' + discBody + '}\n' +
                '};';
        }
        arduinoGenerator.bleChars_ = arduinoGenerator.bleChars_ || {};
        arduinoGenerator.bleSvcIndex = 0;
        let code = `  BLEDevice::init("${nameEsc}");\n`;
        code += `  pServer = BLEDevice::createServer();\n`;
        code += `  pServer->setCallbacks(new BLE_ServerCallbacks());\n`;
        code += arduinoGenerator.statementToCode(block, 'SERVICES') || '';
        code += `  pServer->getAdvertising()->start();\n`;
        return code;
    };

    // 2) Servicio [UUID] ... Características ...
    arduinoGenerator.forBlock['calvin_ble_service'] = function(block) {
        if (!isBleEsp32()) return '';
        const uuid = block.getFieldValue('UUID') || '4fafc201-1fb5-459e-8fcc-c5c9c331914b';
        const idx = arduinoGenerator.bleSvcIndex = (arduinoGenerator.bleSvcIndex || 0);
        arduinoGenerator.bleCurrentService = `pSvc_${idx}`;
        let code = `  BLEService *pSvc_${idx} = pServer->createService("${uuid}");\n`;
        code += arduinoGenerator.statementToCode(block, 'CHARACTERISTICS') || '';
        code += `  pSvc_${idx}->start();\n`;
        arduinoGenerator.bleSvcIndex++;
        return code;
    };

    // 3) Característica [UUID] ... Hacer ...
    arduinoGenerator.forBlock['calvin_ble_characteristic'] = function(block) {
        if (!isBleEsp32()) return '';
        const uuid = block.getFieldValue('UUID') || 'beb5483e-36e1-4688-b7f5-ea07361b26a8';
        const rawName = block.getFieldValue('NAME') || 'cmd';
        const name = sanitizeBleName(rawName);
        const doCode = arduinoGenerator.statementToCode(block, 'DO') || '';
        const cbIdx = (arduinoGenerator.bleCbIndex = (arduinoGenerator.bleCbIndex || 0) + 1) - 1;
        arduinoGenerator.bleChars_ = arduinoGenerator.bleChars_ || {};
        arduinoGenerator.bleChars_[rawName] = name;
        if (!arduinoGenerator.variables_['ble_char_' + name]) {
            arduinoGenerator.variables_['ble_char_' + name] = `BLECharacteristic *pChar_${name} = nullptr;`;
        }
        const doIndent = doCode ? '    ' + doCode.replace(/\n/g, '\n    ') : '';
        const cbClass = `class BLE_CharCallbacks_${cbIdx} : public BLECharacteristicCallbacks {\n` +
            `  void onWrite(BLECharacteristic* p) {\n` +
            `    _ble_last_value = String(p->getValue().c_str());\n` +
            (doCode ? `${doIndent}\n` : '') +
            `  }\n};\n`;
        if (!arduinoGenerator.variables_['ble_cb_' + cbIdx]) {
            arduinoGenerator.variables_['ble_cb_' + cbIdx] = cbClass;
        }
        const svc = arduinoGenerator.bleCurrentService || 'pSvc_0';
        return `  pChar_${name} = ${svc}->createCharacteristic("${uuid}", BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_NOTIFY);\n` +
            `  pChar_${name}->setCallbacks(new BLE_CharCallbacks_${cbIdx}());\n` +
            `  pChar_${name}->addDescriptor(new BLE2902());\n`;
    };

    // 4) ble write [característica] [valor]
    arduinoGenerator.forBlock['calvin_ble_write'] = function(block) {
        const charName = block.getFieldValue('CHAR') || 'cmd';
        const val = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_NONE) || '""';
        if (!isBleEsp32()) {
            return `  // BLE escribir: ${charName} = ${val} (solo ESP32)\n`;
        }
        const name = sanitizeBleName(charName);
        if (!arduinoGenerator.variables_['ble_char_' + name]) {
            arduinoGenerator.variables_['ble_char_' + name] = `BLECharacteristic *pChar_${name} = nullptr;`;
        }
        if (!arduinoGenerator.includes_['ble']) {
            arduinoGenerator.includes_['ble'] = '#include <BLEDevice.h>\n#include <BLEServer.h>\n#include <BLEUtils.h>\n#include <BLE2902.h>';
        }
        return `  if (pChar_${name} != nullptr) { pChar_${name}->setValue(String(${val}).c_str()); pChar_${name}->notify(); }\n`;
    };

    // 5) Valor numérico de esta característica
    arduinoGenerator.forBlock['calvin_ble_char_value_number'] = function(block) {
        if (!isBleEsp32()) {
            return ['0', arduinoGenerator.ORDER_ATOMIC];
        }
        if (!arduinoGenerator.variables_['ble_globals']) {
            arduinoGenerator.variables_['ble_globals'] = 'BLEServer *pServer = nullptr;\nString _ble_last_value;';
        }
        return ['_ble_last_value.toInt()', arduinoGenerator.ORDER_ATOMIC];
    };

    // 6) Valor string de esta característica
    arduinoGenerator.forBlock['calvin_ble_char_value_string'] = function(block) {
        if (!isBleEsp32()) {
            return ['""', arduinoGenerator.ORDER_ATOMIC];
        }
        if (!arduinoGenerator.variables_['ble_globals']) {
            arduinoGenerator.variables_['ble_globals'] = 'BLEServer *pServer = nullptr;\nString _ble_last_value;';
        }
        return ['_ble_last_value', arduinoGenerator.ORDER_ATOMIC];
    };

    // ============================================
    // calvin_io_* - IN/OUT (misma lógica que arduino_*)
    // ============================================
    arduinoGenerator.forBlock['calvin_io_high_low'] = function(block) {
        const val = block.getFieldValue('VAL') || 'HIGH';
        return [val, arduinoGenerator.ORDER_ATOMIC];
    };

    arduinoGenerator.forBlock['calvin_io_digital_write'] = function(block) {
        const pin = block.getFieldValue('PIN');
        const stat = arduinoGenerator.valueToCode(block, 'STAT', arduinoGenerator.ORDER_ATOMIC) || 'HIGH';
        return `  digitalWrite(${pin}, ${stat});\n`;
    };

    arduinoGenerator.forBlock['calvin_io_digital_read'] = function(block) {
        const pin = block.getFieldValue('PIN');
        return [`digitalRead(${pin})`, arduinoGenerator.ORDER_ATOMIC];
    };

    arduinoGenerator.forBlock['calvin_io_analog_read'] = function(block) {
        const pin = block.getFieldValue('PIN');
        return [`analogRead(A${pin})`, arduinoGenerator.ORDER_ATOMIC];
    };

    arduinoGenerator.forBlock['calvin_io_analog_write'] = function(block) {
        const pin = block.getFieldValue('PIN');
        const val = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_ATOMIC) || '0';
        return `  analogWrite(${pin}, ${val});\n`;
    };

    // ============================================
    // calvin_func_* - Funciones
    // ============================================

    // 1) Función sin retorno -> void name() { ... }
    arduinoGenerator.forBlock['calvin_func_defnoreturn'] = function(block) {
        const name = (block.getFieldValue('NAME') || 'miFuncion').replace(/[^a-zA-Z0-9_]/g, '_') || 'miFuncion';
        const body = arduinoGenerator.statementToCode(block, 'STUFF') || '';
        const bodyIndent = body ? '  ' + body.replace(/\n/g, '\n  ') : '';
        const fn = `void ${name}(void) {\n${bodyIndent}\n}`;
        const key = 'calvin_fn_' + name;
        if (!arduinoGenerator.functions_[key]) {
            arduinoGenerator.functions_[key] = fn;
        }
        return '';
    };

    // 2) Función con retorno
    arduinoGenerator.forBlock['calvin_func_defreturn'] = function(block) {
        const name = (block.getFieldValue('NAME') || 'calcular').replace(/[^a-zA-Z0-9_]/g, '_') || 'calcular';
        const type = block.getFieldValue('RETURN_TYPE') || 'int';
        const body = arduinoGenerator.statementToCode(block, 'STUFF') || '';
        const ret = arduinoGenerator.valueToCode(block, 'RETURN', arduinoGenerator.ORDER_ATOMIC) || ('int' === type ? '0' : 'float' === type ? '0.0' : '""');
        const bodyIndent = body ? '  ' + body.replace(/\n/g, '\n  ') : '';
        const fn = `${type} ${name}(void) {\n${bodyIndent}\n  return ${ret};\n}`;
        const key = 'calvin_fn_' + name;
        if (!arduinoGenerator.functions_[key]) {
            arduinoGenerator.functions_[key] = fn;
        }
        return '';
    };

    // 3) Si [condición] return [valor]
    arduinoGenerator.forBlock['calvin_func_ifreturn'] = function(block) {
        const cond = arduinoGenerator.valueToCode(block, 'CONDITION', arduinoGenerator.ORDER_ATOMIC) || 'false';
        const val = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_ATOMIC) || '0';
        return `  if (${cond}) return ${val};\n`;
    };

    // Llamar función sin retorno
    arduinoGenerator.forBlock['calvin_func_call'] = function(block) {
        const name = (block.getFieldValue('NAME') || 'miFuncion').replace(/[^a-zA-Z0-9_]/g, '_') || 'miFuncion';
        return `  ${name}();\n`;
    };

    // Llamar función con retorno
    arduinoGenerator.forBlock['calvin_func_call_return'] = function(block) {
        const name = (block.getFieldValue('NAME') || 'calcular').replace(/[^a-zA-Z0-9_]/g, '_') || 'calcular';
        return [name + '()', arduinoGenerator.ORDER_ATOMIC];
    };

    // ============================================
    // calvin_var_*
    // ============================================
    arduinoGenerator.forBlock['calvin_var_set'] = function(block) {
        const varName = block.getFieldValue('VAR') || 'item';
        const val = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_ASSIGNMENT) || '0';
        return `  ${varName} = ${val};\n`;
    };

    // ============================================
    // calvin_botflow1_* - BotFlow Nivel 1 (CalvinHardware)
    // ============================================

    function isCalvinEsp32() {
        return (arduinoGenerator.boardFqbn || '').includes('esp32');
    }

    function ensureCalvinProximity(pinTrig, pinEcho) {
        const hw = typeof CalvinHardware !== 'undefined' ? CalvinHardware : null;
        if (!hw) return;
        const c = hw.getProximityCode(pinTrig, pinEcho, isCalvinEsp32());
        if (!arduinoGenerator.variables_['calvin_proximidad']) {
            arduinoGenerator.variables_['calvin_proximidad'] = c.defines + '\n' + c.vars + '\n' + c.func;
        }
        if (!arduinoGenerator.setups_['calvin_proximidad']) {
            arduinoGenerator.setups_['calvin_proximidad'] = c.setup;
        }
    }

    function ensureCalvinBuzzer(pin) {
        const hw = typeof CalvinHardware !== 'undefined' ? CalvinHardware : null;
        if (!hw) return;
        const c = hw.getBuzzerCode(pin, isCalvinEsp32());
        if (!arduinoGenerator.variables_['calvin_buzzer']) {
            arduinoGenerator.variables_['calvin_buzzer'] = c.defines + '\n' + c.func;
        }
        if (!arduinoGenerator.setups_['calvin_buzzer']) {
            arduinoGenerator.setups_['calvin_buzzer'] = c.setup;
        }
    }

    function ensureCalvinRgb(pinR, pinG, pinB, tipo) {
        const hw = typeof CalvinHardware !== 'undefined' ? CalvinHardware : null;
        if (!hw) return;
        const c = hw.getRgbCode(pinR, pinG, pinB, tipo, isCalvinEsp32());
        if (!arduinoGenerator.variables_['calvin_rgb']) {
            arduinoGenerator.variables_['calvin_rgb'] = c.defines + '\n' + c.func;
        }
        if (!arduinoGenerator.setups_['calvin_rgb']) {
            arduinoGenerator.setups_['calvin_rgb'] = c.setup;
        }
    }

    function ensureCalvinMotors(pinIzq, pinDer, pwm) {
        const hw = typeof CalvinHardware !== 'undefined' ? CalvinHardware : null;
        if (!hw) return;
        const c = hw.getMotorsCode(pinIzq, pinDer, pwm, isCalvinEsp32());
        if (c.includes && !arduinoGenerator.includes_['calvin_servo']) {
            arduinoGenerator.includes_['calvin_servo'] = c.includes;
        }
        if (!arduinoGenerator.variables_['calvin_motores']) {
            arduinoGenerator.variables_['calvin_motores'] = c.defines + '\n' + c.vars + '\n' + c.func;
        }
        if (!arduinoGenerator.setups_['calvin_motores']) {
            arduinoGenerator.setups_['calvin_motores'] = c.setup;
        }
    }

    const RGB_COLORS = {
        rojo: [255, 0, 0],
        verde: [0, 255, 0],
        azul: [0, 0, 255],
        amarillo: [255, 255, 0],
        cyan: [0, 255, 255],
        magenta: [255, 0, 255],
        blanco: [255, 255, 255]
    };

    arduinoGenerator.forBlock['calvin_botflow1_step'] = function(block) {
        const doCode = arduinoGenerator.statementToCode(block, 'DO') || '';
        return doCode;
    };

    arduinoGenerator.forBlock['calvin_botflow1_init_proximidad'] = function(block) {
        const esp = isCalvinEsp32();
        const trig = esp ? 18 : (block.getFieldValue('TRIG') || 6);
        const echo = esp ? 36 : (block.getFieldValue('ECHO') || 7);
        ensureCalvinProximity(trig, echo);
        return '';
    };

    arduinoGenerator.forBlock['calvin_botflow1_distancia'] = function(block) {
        ensureCalvinProximity();
        return ['calvin_distancia_cm()', arduinoGenerator.ORDER_ATOMIC];
    };

    arduinoGenerator.forBlock['calvin_botflow1_init_nota'] = function(block) {
        const pin = isCalvinEsp32() ? 27 : (block.getFieldValue('PIN') || 3);
        ensureCalvinBuzzer(pin);
        return '';
    };

    arduinoGenerator.forBlock['calvin_botflow1_nota_octava'] = function(block) {
        ensureCalvinBuzzer();
        const nota = block.getFieldValue('NOTA') || 'DO';
        const octava = block.getFieldValue('OCTAVA') || 0;
        const durField = block.getFieldValue('DURACION') || '1';
        const durMs = (durField === 'inf') ? '0' : `(int)((${durField}) * 1000)`;
        const freq = typeof CalvinHardware !== 'undefined' && CalvinHardware.getNoteFreq
            ? CalvinHardware.getNoteFreq(nota, octava) : 262;
        return `  calvin_tocar_nota(${freq}, ${durMs});\n`;
    };

    arduinoGenerator.forBlock['calvin_botflow1_init_rgb'] = function(block) {
        const tipo = block.getFieldValue('TIPO') || 'A';
        const esp = isCalvinEsp32();
        ensureCalvinRgb(esp ? 23 : 5, esp ? 22 : 6, esp ? 21 : 11, tipo);
        return '';
    };

    arduinoGenerator.forBlock['calvin_botflow1_led_color'] = function(block) {
        ensureCalvinRgb();
        const color = block.getFieldValue('COLOR') || 'rojo';
        const rgb = RGB_COLORS[color] || RGB_COLORS.rojo;
        const durField = block.getFieldValue('DURACION') || '1';
        const durMs = (durField === 'inf') ? '0' : `(int)((${durField}) * 1000)`;
        return `  calvin_rgb_encender(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${durMs});\n`;
    };

    arduinoGenerator.forBlock['calvin_botflow1_init_motores'] = function(block) {
        const pwm = block.getFieldValue('PWM') || 220;
        const izq = block.getFieldValue('IZQ') || 9;
        const der = block.getFieldValue('DER') || 10;
        ensureCalvinMotors(izq, der, pwm);
        return '';
    };

    arduinoGenerator.forBlock['calvin_botflow1_adelante'] = function(block) {
        ensureCalvinMotors();
        const seg = arduinoGenerator.valueToCode(block, 'SEG', arduinoGenerator.ORDER_ATOMIC) || '1';
        return `  calvin_motor_adelante(${seg});\n`;
    };

    arduinoGenerator.forBlock['calvin_botflow1_girar_motor'] = function(block) {
        ensureCalvinMotors();
        const lado = block.getFieldValue('LADO') || '0';
        const sentido = block.getFieldValue('SENTIDO') || '0';
        const seg = arduinoGenerator.valueToCode(block, 'SEG', arduinoGenerator.ORDER_ATOMIC) || '1';
        return `  calvin_motor_girar(${lado}, ${sentido}, ${seg});\n`;
    };

    // ============================================
    // calvin_botflow2_* - Sensores de línea
    // ============================================

    function ensureCalvinLineas(pinIzq, pinCent, pinDer) {
        const hw = typeof CalvinHardware !== 'undefined' ? CalvinHardware : null;
        if (!hw) return;
        const c = hw.getLineSensorsCode(pinIzq, pinCent, pinDer, isCalvinEsp32());
        if (!arduinoGenerator.variables_['calvin_lineas']) {
            arduinoGenerator.variables_['calvin_lineas'] = c.defines + '\n' + c.vars + '\n' + c.func;
        }
        if (!arduinoGenerator.setups_['calvin_lineas']) {
            arduinoGenerator.setups_['calvin_lineas'] = c.setup;
        }
    }

    arduinoGenerator.forBlock['calvin_botflow2_condition'] = function(block) {
        const cond = arduinoGenerator.valueToCode(block, 'COND', arduinoGenerator.ORDER_NONE) || 'false';
        const doCode = arduinoGenerator.statementToCode(block, 'DO') || '';
        return `  if (${cond}) {\n${doCode}  }\n`;
    };

    arduinoGenerator.forBlock['calvin_botflow2_init_lineas'] = function(block) {
        const esp = isCalvinEsp32();
        const izq = esp ? 34 : (block.getFieldValue('IZQ') || 0);
        const cent = esp ? 35 : (block.getFieldValue('CENT') || 1);
        const der = esp ? 36 : (block.getFieldValue('DER') || 2);
        ensureCalvinLineas(izq, cent, der);
        return '';
    };

    arduinoGenerator.forBlock['calvin_botflow2_calibrar_lineas'] = function(block) {
        ensureCalvinLineas();
        const n = arduinoGenerator.valueToCode(block, 'N', arduinoGenerator.ORDER_ATOMIC) || '50';
        return `  calvin_linea_calibrar(${n});\n`;
    };

    arduinoGenerator.forBlock['calvin_botflow2_linea_valor'] = function(block) {
        ensureCalvinLineas();
        const lado = block.getFieldValue('LADO') || '0';
        return ['calvin_linea_valor(' + lado + ')', arduinoGenerator.ORDER_ATOMIC];
    };

    arduinoGenerator.forBlock['calvin_botflow2_linea_umbral'] = function(block) {
        ensureCalvinLineas();
        const lado = block.getFieldValue('LADO') || '0';
        return ['calvin_linea_umbral(' + lado + ')', arduinoGenerator.ORDER_ATOMIC];
    };

})();
