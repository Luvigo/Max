"""
Tests de generación de código Calvin.

Valida que calvin_generator.js tenga los handlers esperados y que
las expresiones de generación produzcan patrones de código válido.
También valida definiciones de bloques en calvin_blocks.js.

Categorías: control, operadores, serial, I/O, BotFlow 1, BotFlow 2, BLE.
No testea hardware real. Analiza el código fuente JS.
"""
import re
from pathlib import Path
from django.test import TestCase


def _get_generator_path():
    return Path(__file__).resolve().parent.parent / 'static' / 'editor' / 'js' / 'calvin_generator.js'


def _get_blocks_path():
    return Path(__file__).resolve().parent.parent / 'static' / 'editor' / 'js' / 'calvin_blocks.js'


def _extract_for_block_handlers(content):
    """Extrae bloques registrados en arduinoGenerator.forBlock['...']."""
    return re.findall(r"arduinoGenerator\.forBlock\['([^']+)'\]", content)


def _has_pattern(content, pattern, flags=0):
    """Comprueba si el contenido contiene el patrón."""
    return bool(re.search(pattern, content, flags))


class CalvinGeneratorStructureTest(TestCase):
    """Tests de estructura del generador Calvin."""

    def setUp(self):
        path = _get_generator_path()
        self.assertTrue(path.exists(), f'No existe {path}')
        self.content = path.read_text(encoding='utf-8', errors='replace')

    def test_control_handlers_registered(self):
        """Control: delay, if, if_else, while, for, switch, case, default."""
        handlers = _extract_for_block_handlers(self.content)
        expected = [
            'calvin_control_delay',
            'calvin_control_if',
            'calvin_control_if_else',
            'calvin_control_while',
            'calvin_control_for',
            'calvin_control_switch',
            'calvin_control_case',
            'calvin_control_default',
        ]
        for h in expected:
            self.assertIn(h, handlers, f'Falta handler: {h}')

    def test_operators_handlers_registered(self):
        """Operadores: number, add, subtract, multiply, divide, gt, lt, eq, and, or."""
        handlers = _extract_for_block_handlers(self.content)
        expected = [
            'calvin_operator_number',
            'calvin_operator_add',
            'calvin_operator_subtract',
            'calvin_operator_multiply',
            'calvin_operator_divide',
            'calvin_operator_gt',
            'calvin_operator_lt',
            'calvin_operator_eq',
            'calvin_operator_and',
            'calvin_operator_or',
        ]
        for h in expected:
            self.assertIn(h, handlers, f'Falta handler: {h}')

    def test_serial_handlers_registered(self):
        """Serial: begin, print, has_data, read_string, set_timeout."""
        handlers = _extract_for_block_handlers(self.content)
        expected = [
            'calvin_serial_begin',
            'calvin_serial_print',
            'calvin_serial_has_data',
            'calvin_serial_read_string',
            'calvin_serial_set_timeout',
        ]
        for h in expected:
            self.assertIn(h, handlers, f'Falta handler: {h}')

    def test_io_handlers_registered(self):
        """I/O: digital_write, digital_read, analog_read, analog_write, high_low."""
        handlers = _extract_for_block_handlers(self.content)
        expected = [
            'calvin_io_digital_write',
            'calvin_io_digital_read',
            'calvin_io_analog_read',
            'calvin_io_analog_write',
            'calvin_io_high_low',
        ]
        for h in expected:
            self.assertIn(h, handlers, f'Falta handler: {h}')

    def test_botflow1_handlers_registered(self):
        """BotFlow 1: init_proximidad, init_nota, init_rgb, init_motores, adelante, distancia, nota, led_color."""
        handlers = _extract_for_block_handlers(self.content)
        expected = [
            'calvin_botflow1_init_proximidad',
            'calvin_botflow1_distancia',
            'calvin_botflow1_init_nota',
            'calvin_botflow1_nota_octava',
            'calvin_botflow1_init_rgb',
            'calvin_botflow1_led_color',
            'calvin_botflow1_init_motores',
            'calvin_botflow1_adelante',
            'calvin_botflow1_girar_motor',
        ]
        for h in expected:
            self.assertIn(h, handlers, f'Falta handler: {h}')

    def test_botflow2_handlers_registered(self):
        """BotFlow 2: init_lineas, calibrar, linea_valor, linea_umbral, condition."""
        handlers = _extract_for_block_handlers(self.content)
        expected = [
            'calvin_botflow2_init_lineas',
            'calvin_botflow2_calibrar_lineas',
            'calvin_botflow2_linea_valor',
            'calvin_botflow2_linea_umbral',
            'calvin_botflow2_condition',
        ]
        for h in expected:
            self.assertIn(h, handlers, f'Falta handler: {h}')

    def test_ble_handlers_registered(self):
        """BLE: init, service, characteristic, write, char_value_number, char_value_string."""
        handlers = _extract_for_block_handlers(self.content)
        expected = [
            'calvin_ble_init',
            'calvin_ble_service',
            'calvin_ble_characteristic',
            'calvin_ble_write',
            'calvin_ble_char_value_number',
            'calvin_ble_char_value_string',
        ]
        for h in expected:
            self.assertIn(h, handlers, f'Falta handler: {h}')


class CalvinGeneratorOutputPatternsTest(TestCase):
    """Tests de patrones de salida del generador (análisis del código fuente)."""

    def setUp(self):
        path = _get_generator_path()
        self.content = path.read_text(encoding='utf-8', errors='replace')

    def test_control_delay_generates_delay_call(self):
        """calvin_control_delay debe producir delay(ms)."""
        self.assertTrue(_has_pattern(self.content, r"delay\(\$\{ms\}\)"))

    def test_control_if_generates_if_statement(self):
        """calvin_control_if debe producir if (cond) { ... }."""
        self.assertTrue(_has_pattern(self.content, r"if \(\$\{cond\}\)"))

    def test_serial_begin_generates_serial_begin(self):
        """calvin_serial_begin debe producir Serial.begin(baud)."""
        self.assertTrue(_has_pattern(self.content, r"Serial\.begin\(\$\{baud\}\)"))

    def test_serial_print_generates_println(self):
        """calvin_serial_print debe producir Serial.println(...)."""
        self.assertTrue(_has_pattern(self.content, r"Serial\.println\("))

    def test_io_digital_write_generates_digital_write(self):
        """calvin_io_digital_write debe producir digitalWrite(pin, stat)."""
        self.assertTrue(_has_pattern(self.content, r"digitalWrite\(\$\{pin\}"))

    def test_io_digital_read_generates_digital_read(self):
        """calvin_io_digital_read debe producir digitalRead(pin)."""
        self.assertTrue(_has_pattern(self.content, r"digitalRead\(\$\{pin\}\)"))

    def test_operator_add_generates_addition(self):
        """calvin_operator_add debe producir (a + b)."""
        self.assertTrue(_has_pattern(self.content, r"\(\$\{a\} \+ \$\{b\}\)"))

    def test_init_motores_uses_pwmvalue_and_ensure_calvin_motors(self):
        """calvin_botflow1_init_motores debe usar pwmvalue y ensureCalvinMotors."""
        self.assertTrue(_has_pattern(self.content, r"pwmvalue|PWM"))
        self.assertIn('ensureCalvinMotors', self.content)

    def test_girar_motor_generates_calvin_motor_girar(self):
        """calvin_botflow1_girar_motor debe producir calvin_motor_girar(motor, sentido, tiempo)."""
        self.assertTrue(_has_pattern(self.content, r"calvin_motor_girar\("))

    def test_distancia_returns_value_for_comparison(self):
        """calvin_botflow1_distancia debe devolver calvin_distancia_cm() para uso en if/comparación."""
        self.assertTrue(_has_pattern(self.content, r"calvin_distancia_cm\(\)"),
                        "distancia debe generar calvin_distancia_cm() reutilizable en if/comparación")

    def test_linea_valor_returns_value_for_comparison(self):
        """calvin_botflow2_linea_valor debe devolver calvin_linea_valor(lado) para uso en if/comparación."""
        self.assertTrue(_has_pattern(self.content, r"calvin_linea_valor\("),
                        "linea_valor debe generar calvin_linea_valor() reutilizable en comparación")

    def test_linea_umbral_returns_value_for_comparison(self):
        """calvin_botflow2_linea_umbral debe devolver calvin_linea_umbral(lado) para uso en if/comparación."""
        self.assertTrue(_has_pattern(self.content, r"calvin_linea_umbral\("),
                        "linea_umbral debe generar calvin_linea_umbral() reutilizable en comparación")

    def test_linea_sensors_use_botflow_mapping(self):
        """linea_valor/umbral deben mapear sensor/umbralSensor (s_izquierdo, etc.) a 0/1/2."""
        self.assertIn('sensorLineaToLado', self.content)
        self.assertIn('s_izquierdo', self.content)
        self.assertIn('s_centro', self.content)
        self.assertIn('s_derecho', self.content)


class CalvinBLEESP32Test(TestCase):
    """Tests de generación BLE para ESP32."""

    def setUp(self):
        path = _get_generator_path()
        self.content = path.read_text(encoding='utf-8', errors='replace')

    def test_ble_checks_esp32_via_get_board_family(self):
        """BLE debe comprobar ESP32 con getBoardFamily(currentBoard) === 'esp32'."""
        self.assertTrue(_has_pattern(self.content, r"getBoardFamily\s*\(\s*currentBoard\s*\)\s*===\s*['\"]esp32['\"]"))

    def test_ble_init_includes_bledevice_when_esp32(self):
        """calvin_ble_init debe incluir BLEDevice cuando es ESP32."""
        self.assertIn('#include <BLEDevice.h>', self.content)
        self.assertIn('BLEDevice::init', self.content)

    def test_ble_includes_ble_stack(self):
        """Código BLE debe registrar includes BLEDevice, BLEServer, BLEUtils, BLE2902."""
        self.assertIn('BLEDevice.h', self.content)
        self.assertIn('BLEServer.h', self.content)
        self.assertIn('BLEUtils.h', self.content)
        self.assertIn('BLE2902.h', self.content)


class CalvinMaxUnchangedTest(TestCase):
    """Verifica que el generador Calvin no modifique bloques MAX."""

    def setUp(self):
        path = _get_generator_path()
        self.content = path.read_text(encoding='utf-8', errors='replace')

    def test_no_max_block_modifications(self):
        """calvin_generator no debe registrar handlers para max_* ni arduino_*."""
        handlers = _extract_for_block_handlers(self.content)
        max_handlers = [h for h in handlers if h.startswith('max_') or h.startswith('arduino_')]
        self.assertEqual(len(max_handlers), 0,
                         f'calvin_generator no debe modificar max_*/arduino_*: {max_handlers}')


class MaxBlocksStillWorkTest(TestCase):
    """Verifica que los bloques MAX sigan definidos en arduino_generator (no se rompan)."""

    def setUp(self):
        path = Path(__file__).resolve().parent.parent / 'static' / 'editor' / 'js' / 'arduino_generator.js'
        self.assertTrue(path.exists(), f'No existe {path}')
        self.content = path.read_text(encoding='utf-8', errors='replace')

    def test_max_handlers_exist_in_arduino_generator(self):
        """arduino_generator debe tener handlers para bloques max_* clave."""
        handlers = _extract_for_block_handlers(self.content)
        expected = [
            'max_init_motores',
            'max_adelante',
            'max_medir_distancia',
            'max_tocar_nota',
            'max_leer_linea_izq',
        ]
        for h in expected:
            self.assertIn(h, handlers, f'Bloque MAX {h} debe existir en arduino_generator')

    def test_max_adelante_generates_adelante_call(self):
        """max_adelante debe generar llamada adelante(vel)."""
        self.assertTrue(_has_pattern(self.content, r"adelante\(\$\{vel\}\)"))


# =============================================================================
# CalvinBlocksUpdatedTest - Tests mínimos para bloques Calvin actualizados
# Cobertura: inicializar_motores, girar_motor, inicializar_sensor_distancia,
# leer_sensor_distancia, inicializar_sensor_linea, calibrar_sensores_linea,
# leer_sensores_linea, umbral_sensor, ble_init, ble_service, ble_characteristic.
# Valida: block types, fields/inputs, generador código no vacío, setup una vez.
# =============================================================================

_CALVIN_UPDATED_BLOCKS = [
    ('calvin_botflow1_init_motores', 'inicializar_motores', ['pwmvalue']),
    ('calvin_botflow1_girar_motor', 'girar_motor', ['motor', 'sentido', 'TIEMPO']),
    ('calvin_botflow1_init_proximidad', 'inicializar_sensor_distancia', []),
    ('calvin_botflow1_distancia', 'leer_sensor_distancia', []),
    ('calvin_botflow2_init_lineas', 'inicializar_sensor_linea', []),
    ('calvin_botflow2_calibrar_lineas', 'calibrar_sensores_linea', ['ciclos']),
    ('calvin_botflow2_linea_valor', 'leer_sensores_linea', ['sensor']),
    ('calvin_botflow2_linea_umbral', 'umbral_sensor', ['umbralSensor']),
    ('calvin_ble_init', 'ble_init', ['NOMBRE', 'onConectado', 'onDesconectado', 'SERVICES']),
    ('calvin_ble_service', 'ble_service', ['NOMBRE', 'UUID', 'CHARACTERISTICS']),
    ('calvin_ble_characteristic', 'ble_characteristic', ['NOMBRE', 'UUID', 'onWrite']),
]


class CalvinBlocksUpdatedTest(TestCase):
    """Tests mínimos para bloques Calvin actualizados. No testea hardware real."""

    def setUp(self):
        self.blocks_path = _get_blocks_path()
        self.generator_path = _get_generator_path()
        self.assertTrue(self.blocks_path.exists(), f'No existe {self.blocks_path}')
        self.assertTrue(self.generator_path.exists(), f'No existe {self.generator_path}')
        self.blocks_content = self.blocks_path.read_text(encoding='utf-8', errors='replace')
        self.generator_content = self.generator_path.read_text(encoding='utf-8', errors='replace')

    def _block_def_regex(self, block_type):
        """Patrón para encontrar definición del bloque."""
        escaped = re.escape(f"Blockly.Blocks['{block_type}']")
        return re.compile(escaped, re.MULTILINE)

    def test_block_types_exist_in_blocks_js(self):
        """Todos los block types actualizados deben existir en calvin_blocks.js."""
        for block_type, _alias, _fields in _CALVIN_UPDATED_BLOCKS:
            with self.subTest(block=block_type):
                self.assertTrue(
                    _has_pattern(self.blocks_content, self._block_def_regex(block_type).pattern),
                    f'Bloque {block_type} debe estar definido en calvin_blocks.js'
                )

    def test_block_types_have_generator_handlers(self):
        """Todos los block types deben tener handler en calvin_generator.js."""
        for block_type, _alias, _fields in _CALVIN_UPDATED_BLOCKS:
            with self.subTest(block=block_type):
                pattern = re.escape(f"arduinoGenerator.forBlock['{block_type}']")
                self.assertTrue(
                    _has_pattern(self.generator_content, pattern),
                    f'Handler para {block_type} debe existir en calvin_generator.js'
                )

    def test_key_fields_exist_in_block_definitions(self):
        """Los campos principales deben aparecer en la definición del bloque."""
        for block_type, _alias, fields in _CALVIN_UPDATED_BLOCKS:
            if not fields:
                continue
            marker = f"Blockly.Blocks['{block_type}']"
            pos = self.blocks_content.find(marker)
            self.assertNotEqual(pos, -1, f'Bloque {block_type} no encontrado')
            chunk = self.blocks_content[pos:pos + 1200]
            for field in fields:
                with self.subTest(block=block_type, field=field):
                    self.assertTrue(
                        f'"{field}"' in chunk or field in chunk,
                        f'Campo/input {field} debe existir en bloque {block_type}',
                    )

    def test_generator_produces_non_empty_code(self):
        """El generador debe producir código para cada bloque (patrones esperados)."""
        expected_outputs = [
            ('calvin_botflow1_init_motores', r'ensureCalvinMotors|calvin_motor'),
            ('calvin_botflow1_girar_motor', r'calvin_motor_girar\('),
            ('calvin_botflow1_init_proximidad', r'ensureCalvinProximity|calvin_proximidad'),
            ('calvin_botflow1_distancia', r"calvin_distancia_cm\(\)"),
            ('calvin_botflow2_init_lineas', r'ensureCalvinLineas|calvin_lineas'),
            ('calvin_botflow2_calibrar_lineas', r'calvin_linea_calibrar\('),
            ('calvin_botflow2_linea_valor', r'calvin_linea_valor\('),
            ('calvin_botflow2_linea_umbral', r'calvin_linea_umbral\('),
            ('calvin_ble_init', r'BLEDevice::init|ble'),
            ('calvin_ble_service', r'createService|pSvc_'),
            ('calvin_ble_characteristic', r'createCharacteristic|pChar_'),
        ]
        for block_type, pattern in expected_outputs:
            with self.subTest(block=block_type):
                self.assertTrue(
                    _has_pattern(self.generator_content, pattern),
                    f'Generador para {block_type} debe producir código con patrón {pattern}',
                )

    def test_setup_helpers_registered_once(self):
        """Los setup/helpers Calvin deben registrarse solo una vez (!arduinoGenerator.xxx_['key'])."""
        # Patrón: if (!arduinoGenerator.variables_['calvin_xxx']) { ... }
        single_reg_vars = [
            'calvin_proximidad', 'calvin_buzzer', 'calvin_rgb', 'calvin_motores', 'calvin_lineas',
        ]
        for key in single_reg_vars:
            with self.subTest(variable=key):
                pattern = rf"!arduinoGenerator\.variables_\['{re.escape(key)}'\]"
                self.assertTrue(
                    _has_pattern(self.generator_content, pattern),
                    f'variables_["{key}"] debe registrarse una sola vez',
                )
        single_reg_setups = [
            'calvin_proximidad', 'calvin_buzzer', 'calvin_rgb', 'calvin_motores', 'calvin_lineas',
        ]
        for key in single_reg_setups:
            with self.subTest(setup=key):
                pattern = rf"!arduinoGenerator\.setups_\['{re.escape(key)}'\]"
                self.assertTrue(
                    _has_pattern(self.generator_content, pattern),
                    f'setups_["{key}"] debe registrarse una sola vez',
                )

    def test_generator_has_forBlock_registry(self):
        """El generador debe registrar handlers en arduinoGenerator.forBlock."""
        self.assertIn('arduinoGenerator.forBlock', self.generator_content)
        handlers = _extract_for_block_handlers(self.generator_content)
        self.assertGreater(len(handlers), 10, 'Debe haber múltiples handlers Calvin')
