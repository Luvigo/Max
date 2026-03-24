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

    // 2) serial_timeout -> Serial.setTimeout(ms)
    arduinoGenerator.forBlock['calvin_serial_set_timeout'] = function(block) {
        const ms = arduinoGenerator.valueToCode(block, 'TIMEOUT', arduinoGenerator.ORDER_ATOMIC) ||
            arduinoGenerator.valueToCode(block, 'MS', arduinoGenerator.ORDER_ATOMIC) || '10';
        return `  Serial.setTimeout(${ms});\n`;
    };

    // 3) serial_print -> Serial.println
    arduinoGenerator.forBlock['calvin_serial_print'] = function(block) {
        const val = arduinoGenerator.valueToCode(block, 'CONTENT', arduinoGenerator.ORDER_NONE) ||
            arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_NONE) || '""';
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

    // 1) Inicializar BLE (BotFlow: NOMBRE value, onConectado, onDesconectado)
    arduinoGenerator.forBlock['calvin_ble_init'] = function(block) {
        const nameCode = arduinoGenerator.valueToCode(block, 'NOMBRE', arduinoGenerator.ORDER_ATOMIC) || '"CalvinBot"';
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
        const connectedCode = (arduinoGenerator.statementToCode(block, 'onConectado') || arduinoGenerator.statementToCode(block, 'CONNECTED') || '').trim();
        const disconnectedCode = (arduinoGenerator.statementToCode(block, 'onDesconectado') || arduinoGenerator.statementToCode(block, 'DISCONNECTED') || '').trim();
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
        let code = `  BLEDevice::init(${nameCode});\n`;
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

    // 3) Característica [NOMBRE] [UUID] onWrite (BotFlow)
    arduinoGenerator.forBlock['calvin_ble_characteristic'] = function(block) {
        if (!isBleEsp32()) return '';
        const uuid = block.getFieldValue('UUID') || 'beb5483e-36e1-4688-b7f5-ea07361b26a8';
        const rawName = block.getFieldValue('NOMBRE') || block.getFieldValue('NAME') || 'cmd';
        const name = sanitizeBleName(rawName);
        const doCode = arduinoGenerator.statementToCode(block, 'onWrite') || arduinoGenerator.statementToCode(block, 'DO') || '';
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

    // 4) ble_characteristic_write (BotFlow: ble write [SERVICIO] [CARACTERISTICA] to [VALUE])
    arduinoGenerator.forBlock['calvin_ble_write'] = function(block) {
        const charName = block.getFieldValue('CARACTERISTICA') || block.getFieldValue('CHAR') || 'cmd';
        const charNameResolved = (charName === 'nothing_selected') ? 'cmd' : charName;
        const val = arduinoGenerator.valueToCode(block, 'VALUE', arduinoGenerator.ORDER_NONE) || '""';
        if (!isBleEsp32()) {
            return `  // BLE escribir: ${charNameResolved} = ${val} (solo ESP32)\n`;
        }
        const name = sanitizeBleName(charNameResolved);
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

    function getCalvinFuncParams(block) {
        const p = block.paramNames_;
        return Array.isArray(p) ? p : [];
    }

    // 1) Función sin retorno -> void name(int x, ...) { ... }
    arduinoGenerator.forBlock['calvin_func_defnoreturn'] = function(block) {
        const name = (block.getFieldValue('NAME') || 'do something').replace(/[^a-zA-Z0-9_]/g, '_') || 'do_something';
        const params = getCalvinFuncParams(block);
        const sig = params.length > 0
            ? params.map(function(p) { return 'int ' + (p.replace(/[^a-zA-Z0-9_]/g, '_') || 'x'); }).join(', ')
            : 'void';
        const body = arduinoGenerator.statementToCode(block, 'STUFF') || '';
        const bodyIndent = body ? '  ' + body.replace(/\n/g, '\n  ') : '';
        const fn = `void ${name}(${sig}) {\n${bodyIndent}\n}`;
        const key = 'calvin_fn_' + name;
        if (!arduinoGenerator.functions_[key]) {
            arduinoGenerator.functions_[key] = fn;
        }
        return '';
    };

    // 2) Función con retorno
    arduinoGenerator.forBlock['calvin_func_defreturn'] = function(block) {
        const name = (block.getFieldValue('NAME') || 'do something2').replace(/[^a-zA-Z0-9_]/g, '_') || 'do_something2';
        const type = block.getFieldValue('RETURN_TYPE') || 'int';
        const params = getCalvinFuncParams(block);
        const sig = params.length > 0
            ? params.map(function(p) { return 'int ' + (p.replace(/[^a-zA-Z0-9_]/g, '_') || 'x'); }).join(', ')
            : 'void';
        const body = arduinoGenerator.statementToCode(block, 'STUFF') || '';
        const ret = arduinoGenerator.valueToCode(block, 'RETURN', arduinoGenerator.ORDER_ATOMIC) || ('int' === type ? '0' : 'float' === type ? '0.0' : '""');
        const bodyIndent = body ? '  ' + body.replace(/\n/g, '\n  ') : '';
        const fn = `${type} ${name}(${sig}) {\n${bodyIndent}\n  return ${ret};\n}`;
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
        const name = (block.getFieldValue('NAME') || 'do something').replace(/[^a-zA-Z0-9_]/g, '_') || 'do_something';
        const n = block.argCount_ | 0;
        let args = '';
        for (let i = 0; i < n; i++) {
            const v = arduinoGenerator.valueToCode(block, 'ARG' + i, arduinoGenerator.ORDER_ATOMIC) || '0';
            args += (i > 0 ? ', ' : '') + v;
        }
        return `  ${name}(${args});\n`;
    };

    // Llamar función con retorno
    arduinoGenerator.forBlock['calvin_func_call_return'] = function(block) {
        const name = (block.getFieldValue('NAME') || 'do something2').replace(/[^a-zA-Z0-9_]/g, '_') || 'do_something2';
        const n = block.argCount_ | 0;
        let args = '';
        for (let i = 0; i < n; i++) {
            const v = arduinoGenerator.valueToCode(block, 'ARG' + i, arduinoGenerator.ORDER_ATOMIC) || '0';
            args += (i > 0 ? ', ' : '') + v;
        }
        return [name + '(' + args + ')', arduinoGenerator.ORDER_ATOMIC];
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

    /** Indica si el bloque está dentro de arduino_setup (no en loop ni suelto). */
    function isBlockInSetup(block) {
        if (!block) return false;
        let b = block;
        while (b) {
            if (b.type === 'arduino_setup') return true;
            if (b.type === 'arduino_loop') return false;
            b = b.getParent && b.getParent();
        }
        return false;
    }

    function ensureCalvinProximity(pinTrig, pinEcho, addSetup) {
        const hw = typeof CalvinHardware !== 'undefined' ? CalvinHardware : null;
        if (!hw) return;
        const c = hw.getProximityCode(pinTrig, pinEcho, isCalvinEsp32());
        if (!arduinoGenerator.variables_['calvin_proximidad']) {
            arduinoGenerator.variables_['calvin_proximidad'] = c.defines + '\n' + c.vars + '\n' + c.func;
        }
        if (addSetup && !arduinoGenerator.setups_['calvin_proximidad']) {
            arduinoGenerator.setups_['calvin_proximidad'] = c.setup;
        }
    }

    function ensureCalvinBuzzer(pin, addSetup) {
        const hw = typeof CalvinHardware !== 'undefined' ? CalvinHardware : null;
        if (!hw) return;
        const c = hw.getBuzzerCode(pin, isCalvinEsp32());
        if (!arduinoGenerator.variables_['calvin_buzzer']) {
            arduinoGenerator.variables_['calvin_buzzer'] = c.defines + '\n' + c.func;
        }
        if (addSetup && !arduinoGenerator.setups_['calvin_buzzer']) {
            arduinoGenerator.setups_['calvin_buzzer'] = c.setup;
        }
    }

    function ensureCalvinRgb(pinR, pinG, pinB, tipo, addSetup) {
        const hw = typeof CalvinHardware !== 'undefined' ? CalvinHardware : null;
        if (!hw) return;
        const c = hw.getRgbCode(pinR, pinG, pinB, tipo, isCalvinEsp32());
        if (!arduinoGenerator.variables_['calvin_rgb']) {
            arduinoGenerator.variables_['calvin_rgb'] = c.defines + '\n' + c.func;
        }
        if (addSetup && !arduinoGenerator.setups_['calvin_rgb']) {
            arduinoGenerator.setups_['calvin_rgb'] = c.setup;
        }
    }

    /** @param {boolean} [addSetup] Si true, añade setup. Solo cuando el bloque init está dentro de arduino_setup. */
    function ensureCalvinMotors(pinIzq, pinDer, pwm, addSetup) {
        const hw = typeof CalvinHardware !== 'undefined' ? CalvinHardware : null;
        if (!hw) return;
        const c = hw.getMotorsCode(pinIzq, pinDer, pwm, isCalvinEsp32());
        if (c.includes && !arduinoGenerator.includes_['calvin_servo']) {
            arduinoGenerator.includes_['calvin_servo'] = c.includes;
        }
        if (!arduinoGenerator.variables_['calvin_motores']) {
            arduinoGenerator.variables_['calvin_motores'] = c.defines + '\n' + c.vars + '\n' + c.func;
        }
        // Solo añadir setup cuando existe el bloque Inicializar Motores (código refleja bloques)
        if (addSetup && !arduinoGenerator.setups_['calvin_motores']) {
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

    arduinoGenerator.forBlock['calvin_botflow1_init_proximidad'] = function(block) {
        const esp = isCalvinEsp32();
        const hw = typeof CalvinHardware !== 'undefined' ? CalvinHardware : null;
        const pins = hw ? (esp ? hw.PINS_ESP32 : hw.PINS) : null;
        const trig = pins ? pins.PROX_TRIG : (esp ? 18 : 6);
        const echo = pins ? pins.PROX_ECHO : (esp ? 36 : 7);
        ensureCalvinProximity(trig, echo, isBlockInSetup(block));
        return '';
    };

    arduinoGenerator.forBlock['calvin_botflow1_distancia'] = function(block) {
        ensureCalvinProximity(undefined, undefined, false);
        return ['calvin_distancia_cm()', arduinoGenerator.ORDER_ATOMIC];
    };

    arduinoGenerator.forBlock['calvin_botflow1_init_nota'] = function(block) {
        const esp = isCalvinEsp32();
        const hw = typeof CalvinHardware !== 'undefined' ? CalvinHardware : null;
        const pins = hw ? (esp ? hw.PINS_ESP32 : hw.PINS) : null;
        const pin = pins ? pins.BUZZER : (esp ? 27 : 3);
        ensureCalvinBuzzer(pin, isBlockInSetup(block));
        return '';
    };

    const NOTA_TO_CALVIN = { NOTE_C: 'DO', NOTE_D: 'RE', NOTE_E: 'MI', NOTE_F: 'FA', NOTE_G: 'SOL', NOTE_A: 'LA', NOTE_B: 'SI' };

    arduinoGenerator.forBlock['calvin_botflow1_nota_octava'] = function(block) {
        ensureCalvinBuzzer(undefined, false);
        const notaVal = block.getFieldValue('nota') || block.getFieldValue('NOTA') || 'NOTE_C';
        const nota = NOTA_TO_CALVIN[notaVal] || notaVal;
        const octava = block.getFieldValue('octava') || block.getFieldValue('OCTAVA') || 0;
        const durField = block.getFieldValue('durnota') || block.getFieldValue('DURACION') || '1';
        const durMs = (durField === 'inf') ? '0' : `(int)((${durField}) * 1000)`;
        const freq = typeof CalvinHardware !== 'undefined' && CalvinHardware.getNoteFreq
            ? CalvinHardware.getNoteFreq(nota, octava) : 262;
        return `  calvin_tocar_nota(${freq}, ${durMs});\n`;
    };

    arduinoGenerator.forBlock['calvin_botflow1_init_rgb'] = function(block) {
        const tipo = block.getFieldValue('tipoLED') || block.getFieldValue('TIPO') || 'A';
        const esp = isCalvinEsp32();
        const hw = typeof CalvinHardware !== 'undefined' ? CalvinHardware : null;
        const pins = hw ? (esp ? hw.PINS_ESP32 : hw.PINS) : null;
        const r = pins ? pins.RGB_R : (esp ? 23 : 5);
        const g = pins ? pins.RGB_G : (esp ? 22 : 6);
        const b = pins ? pins.RGB_B : (esp ? 21 : 11);
        ensureCalvinRgb(r, g, b, tipo, isBlockInSetup(block));
        return '';
    };

    arduinoGenerator.forBlock['calvin_botflow1_led_color'] = function(block) {
        ensureCalvinRgb(undefined, undefined, undefined, undefined, false);
        const estado = block.getFieldValue('estado') || block.getFieldValue('ESTADO') || 'true';
        const color = block.getFieldValue('color') || block.getFieldValue('COLOR') || 'rojo';
        const durField = block.getFieldValue('durled') || block.getFieldValue('DURACION') || '1';
        const durMs = (durField === 'inf') ? '0' : `(int)((${durField}) * 1000)`;
        if (estado === 'false') {
            return `  calvin_rgb_encender(0, 0, 0, ${durMs});\n`;
        }
        const rgb = RGB_COLORS[color] || RGB_COLORS.rojo;
        return `  calvin_rgb_encender(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${durMs});\n`;
    };

    arduinoGenerator.forBlock['calvin_botflow1_init_motores'] = function(block) {
        const pwm = block.getFieldValue('pwmvalue') || block.getFieldValue('PWM') || 220;
        ensureCalvinMotors(undefined, undefined, pwm, isBlockInSetup(block));
        return '';
    };

    arduinoGenerator.forBlock['calvin_botflow1_adelante'] = function(block) {
        ensureCalvinMotors(undefined, undefined, undefined, false);
        const seg = arduinoGenerator.valueToCode(block, 'SEG', arduinoGenerator.ORDER_ATOMIC) || '1';
        return `  calvin_mover(1, ${seg});\n`;
    };

    arduinoGenerator.forBlock['calvin_botflow1_mover'] = function(block) {
        ensureCalvinMotors(undefined, undefined, undefined, false);
        const movimiento = block.getFieldValue('movimiento') || '1';
        const tiempo = arduinoGenerator.valueToCode(block, 'TIEMPO', arduinoGenerator.ORDER_ATOMIC) ||
            arduinoGenerator.valueToCode(block, 'SEG', arduinoGenerator.ORDER_ATOMIC) || '1';
        return `  calvin_mover(${movimiento}, ${tiempo});\n`;
    };

    arduinoGenerator.forBlock['calvin_botflow1_girar_motor'] = function(block) {
        ensureCalvinMotors(undefined, undefined, undefined, false);
        const motor = block.getFieldValue('motor') ?? block.getFieldValue('LADO') ?? '0';
        const sentidoBotFlow = block.getFieldValue('sentido') ?? block.getFieldValue('SENTIDO') ?? '0';
        const tiempo = arduinoGenerator.valueToCode(block, 'TIEMPO', arduinoGenerator.ORDER_ATOMIC) ||
            arduinoGenerator.valueToCode(block, 'SEG', arduinoGenerator.ORDER_ATOMIC) || '1';
        const sentido = (sentidoBotFlow === '1') ? '0' : '1';
        return `  calvin_motor_girar(${motor}, ${sentido}, ${tiempo});\n`;
    };

    // ============================================
    // calvin_botflow2_* - Sensores de línea
    // ============================================

    function ensureCalvinLineas(pinIzq, pinCent, pinDer, addSetup) {
        const hw = typeof CalvinHardware !== 'undefined' ? CalvinHardware : null;
        if (!hw) return;
        const c = hw.getLineSensorsCode(pinIzq, pinCent, pinDer, isCalvinEsp32());
        if (!arduinoGenerator.variables_['calvin_lineas']) {
            arduinoGenerator.variables_['calvin_lineas'] = c.defines + '\n' + c.vars + '\n' + c.func;
        }
        if (addSetup && !arduinoGenerator.setups_['calvin_lineas']) {
            arduinoGenerator.setups_['calvin_lineas'] = c.setup;
        }
    }

    arduinoGenerator.forBlock['calvin_botflow2_init_lineas'] = function(block) {
        const esp = isCalvinEsp32();
        const hw = typeof CalvinHardware !== 'undefined' ? CalvinHardware : null;
        const pins = hw ? (esp ? hw.PINS_ESP32 : hw.PINS) : null;
        const izq = pins ? pins.LINEA_IZQ : (esp ? 34 : 0);
        const cent = pins ? pins.LINEA_CENT : (esp ? 35 : 1);
        const der = pins ? pins.LINEA_DER : (esp ? 36 : 2);
        ensureCalvinLineas(izq, cent, der, isBlockInSetup(block));
        return '';
    };

    arduinoGenerator.forBlock['calvin_botflow2_calibrar_lineas'] = function(block) {
        ensureCalvinLineas(undefined, undefined, undefined, false);
        const ciclos = block.getFieldValue('ciclos') || '30';
        return `  calvin_linea_calibrar(${ciclos});\n`;
    };

    /** Mapea sensor BotFlow (s_izquierdo/s_centro/s_derecho) o LADO (0/1/2) al índice C. */
    function sensorLineaToLado(val) {
        if (val === 's_izquierdo' || val === '0') return '0';
        if (val === 's_centro' || val === '1') return '1';
        if (val === 's_derecho' || val === '2') return '2';
        return '0';
    }

    arduinoGenerator.forBlock['calvin_botflow2_linea_valor'] = function(block) {
        ensureCalvinLineas(undefined, undefined, undefined, false);
        const sensor = block.getFieldValue('sensor') || block.getFieldValue('LADO') || 's_izquierdo';
        const lado = sensorLineaToLado(sensor);
        return ['calvin_linea_valor(' + lado + ')', arduinoGenerator.ORDER_ATOMIC];
    };

    arduinoGenerator.forBlock['calvin_botflow2_linea_umbral'] = function(block) {
        ensureCalvinLineas(undefined, undefined, undefined, false);
        const sensor = block.getFieldValue('umbralSensor') || block.getFieldValue('LADO') || 's_izquierdo';
        const lado = sensorLineaToLado(sensor);
        return ['calvin_linea_umbral(' + lado + ')', arduinoGenerator.ORDER_ATOMIC];
    };

    // Apagar LED al inicio de cada iteración cuando se usa RGB (evita estado residual/verde)
    arduinoGenerator.forBlock['arduino_loop'] = function(block) {
        const statements = arduinoGenerator.statementToCode(block, 'LOOP_CODE');
        let prefix = '';
        if (arduinoGenerator.variables_ && arduinoGenerator.variables_['calvin_rgb']) {
            prefix = '  calvin_rgb_encender(0, 0, 0, 0);\n';
        }
        return 'void loop() {\n' + prefix + statements + '}\n';
    };

})();
