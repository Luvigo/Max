"""
Tests del selector MAX/Calvin y estructura del toolbox.

Valida que:
- Modo MAX muestra bloques max_* y no calvin_*
- Modo Calvin muestra bloques calvin_* y no max_*
- ToolboxConfig expone la API esperada

No testea hardware real. No usa DOM real.
"""
import re
from pathlib import Path
from django.test import TestCase


def _get_toolbox_config_path():
    return Path(__file__).resolve().parent.parent / 'static' / 'editor' / 'js' / 'toolbox_config.js'


def _get_app_js_path():
    return Path(__file__).resolve().parent.parent / 'static' / 'editor' / 'js' / 'app.js'


def _extract_toolbox_section(content, name):
    """Extrae el contenido de TOOLBOX_MAX o TOOLBOX_CALVIN del JS."""
    pattern = rf'const {name} = `(.*?)`;'
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else ''


def _get_block_types(xml_content):
    """Extrae todos los block type= del XML."""
    return re.findall(r'block type="([^"]+)"', xml_content)


class ToolboxMaxCalvinTest(TestCase):
    """Tests de estructura del toolbox por modo robot."""

    def setUp(self):
        config_path = _get_toolbox_config_path()
        self.assertTrue(config_path.exists(), f'No existe {config_path}')
        self.content = config_path.read_text(encoding='utf-8', errors='replace')

    def test_toolbox_max_contains_max_blocks(self):
        """Modo MAX: debe incluir bloques max_*."""
        toolbox_max = _extract_toolbox_section(self.content, 'TOOLBOX_MAX')
        self.assertNotEqual(toolbox_max, '', 'TOOLBOX_MAX no debe estar vacío')
        block_types = _get_block_types(toolbox_max)
        max_blocks = [t for t in block_types if t.startswith('max_')]
        self.assertGreater(len(max_blocks), 0, 'TOOLBOX_MAX debe contener al menos un bloque max_*')
        self.assertIn('max_init_motores', block_types)
        self.assertIn('max_medir_distancia', block_types)
        self.assertIn('max_adelante', block_types)

    def test_toolbox_max_excludes_calvin_blocks(self):
        """Modo MAX: no debe incluir bloques calvin_* en la sección MAX."""
        toolbox_max = _extract_toolbox_section(self.content, 'TOOLBOX_MAX')
        block_types = _get_block_types(toolbox_max)
        calvin_blocks = [t for t in block_types if t.startswith('calvin_')]
        self.assertEqual(len(calvin_blocks), 0, 
                         f'TOOLBOX_MAX no debe contener calvin_*: {calvin_blocks}')

    def test_toolbox_calvin_contains_calvin_blocks(self):
        """Modo Calvin: debe incluir bloques calvin_*."""
        toolbox_calvin = _extract_toolbox_section(self.content, 'TOOLBOX_CALVIN')
        self.assertNotEqual(toolbox_calvin, '', 'TOOLBOX_CALVIN no debe estar vacío')
        block_types = _get_block_types(toolbox_calvin)
        calvin_blocks = [t for t in block_types if t.startswith('calvin_')]
        self.assertGreater(len(calvin_blocks), 0, 'TOOLBOX_CALVIN debe contener bloques calvin_*')
        self.assertIn('base_delay', block_types)
        self.assertIn('switch_case', block_types)
        self.assertIn('case', block_types)
        self.assertIn('controls_whileUntil', block_types)
        self.assertIn('controls_for', block_types)
        self.assertIn('controls_if', block_types)
        self.assertIn('controls_ifelse', block_types)
        self.assertIn('math_number', block_types)
        self.assertIn('sumar', block_types)
        self.assertIn('restar', block_types)
        self.assertIn('multiplicar', block_types)
        self.assertIn('dividir', block_types)
        self.assertIn('math_random_int', block_types)
        self.assertIn('mayor_que', block_types)
        self.assertIn('menor_que', block_types)
        self.assertIn('igual_que', block_types)
        self.assertIn('logica_y', block_types)
        self.assertIn('logica_o', block_types)
        self.assertIn('math_single', block_types)
        self.assertIn('logic_compare', block_types)
        self.assertIn('logic_negate', block_types)
        self.assertIn('logic_operation', block_types)
        self.assertIn('serial_init', block_types)
        self.assertIn('inout_highlow', block_types)
        self.assertIn('inout_digital_write', block_types)
        self.assertIn('inout_digital_read', block_types)
        self.assertIn('inout_analog_read', block_types)
        self.assertIn('inout_analog_write', block_types)
        self.assertIn('text', block_types)
        self.assertIn('calvin_ble_init', block_types)
        self.assertIn('calvin_botflow1_init_proximidad', block_types)
        self.assertIn('calvin_botflow2_init_lineas', block_types)

    def test_toolbox_calvin_excludes_max_blocks(self):
        """Modo Calvin: no debe incluir bloques max_* en la sección Calvin."""
        toolbox_calvin = _extract_toolbox_section(self.content, 'TOOLBOX_CALVIN')
        block_types = _get_block_types(toolbox_calvin)
        max_blocks = [t for t in block_types if t.startswith('max_')]
        self.assertEqual(len(max_blocks), 0,
                         f'TOOLBOX_CALVIN no debe contener max_*: {max_blocks}')

    def test_toolbox_config_exports_expected_api(self):
        """ToolboxConfig debe exponer getStoredRobot, setStoredRobot, getToolboxXml, buildToolboxElement."""
        self.assertIn('getStoredRobot', self.content)
        self.assertIn('setStoredRobot', self.content)
        self.assertIn('getToolboxXml', self.content)
        self.assertIn('buildToolboxElement', self.content)
        self.assertIn('hasCrossRobotBlocks', self.content)
        self.assertIn('ROBOT_KEY', self.content)

    def test_get_toolbox_xml_logic_max(self):
        """getToolboxXml('MAX') debe concatenar BASE + MAX + AVANZADO."""
        self.assertIn("(robot === 'Calvin') ? TOOLBOX_CALVIN : TOOLBOX_MAX", self.content)

    def test_calvin_categories_present(self):
        """Calvin toolbox debe tener categorías: Control, Operadores, Serial, BLE, I/O, BotFlow 1, BotFlow 2."""
        toolbox_calvin = _extract_toolbox_section(self.content, 'TOOLBOX_CALVIN')
        expected_categories = [
            'Calvin Control', 'Calvin Operadores', 'Calvin Texto', 'Calvin Serial',
            'Calvin BLE', 'Calvin I/O', 'Calvin Funciones', 'Calvin Variables',
            'Calvin BotFlow Nivel 1', 'Calvin BotFlow Nivel 2'
        ]
        for cat in expected_categories:
            self.assertIn(cat, toolbox_calvin, f'Falta categoría: {cat}')

    def test_calvin_variables_flyout_buttons(self):
        """Calvin Variables: categoría custom + callbacks en app.js (flyout dinámico Botflow)."""
        toolbox_calvin = _extract_toolbox_section(self.content, 'TOOLBOX_CALVIN')
        self.assertIn('custom="CALVIN_VARIABLES_FLYOUT"', toolbox_calvin)
        self.assertIn('Calvin Variables', toolbox_calvin)

        app_path = _get_app_js_path()
        self.assertTrue(app_path.exists(), f'No existe {app_path}')
        app_content = app_path.read_text(encoding='utf-8', errors='replace')
        self.assertIn("registerToolboxCategoryCallback('CALVIN_VARIABLES_FLYOUT'", app_content)
        for key in ('calvin_btn_var_string', 'calvin_btn_var_int', 'calvin_btn_var_color'):
            self.assertIn(f"registerButtonCallback('{key}'", app_content,
                          f'Falta registerButtonCallback para {key}')
        self.assertIn('addButtonJson', app_content)
        self.assertIn('callbackkey', app_content.lower())
        self.assertIn("addButtonJson('Crear variable numérica'", app_content)
        self.assertIn("addButtonJson('Crear variable de color'", app_content)

    def test_calvin_functions_flyout_dynamic(self):
        """Calvin Funciones: categoría custom + callback que lista llamadas por definición."""
        toolbox_calvin = _extract_toolbox_section(self.content, 'TOOLBOX_CALVIN')
        self.assertIn('custom="CALVIN_FUNCTIONS_FLYOUT"', toolbox_calvin)
        self.assertIn('Calvin Funciones', toolbox_calvin)

        app_path = _get_app_js_path()
        self.assertTrue(app_path.exists(), f'No existe {app_path}')
        app_content = app_path.read_text(encoding='utf-8', errors='replace')
        self.assertIn("registerToolboxCategoryCallback('CALVIN_FUNCTIONS_FLYOUT'", app_content)
        self.assertIn('calvinFunctionsFlyoutCategory', app_content)
        self.assertIn('calvinCollectProcedureDefinitions', app_content)

    def test_calvin_io_toolbox_defaults_esp32_led_r(self):
        """Calvin I/O: pines por defecto LED R (23), no 13, para pruebas visibles en el carro."""
        toolbox_calvin = _extract_toolbox_section(self.content, 'TOOLBOX_CALVIN')
        self.assertIn('inout_digital_write', toolbox_calvin)
        self.assertGreaterEqual(toolbox_calvin.count('<field name="PIN">23</field>'), 3)
        self.assertNotIn('<field name="PIN">13</field>', toolbox_calvin)
        self.assertIn('<field name="PIN">A0</field>', toolbox_calvin)
        hw = Path(__file__).resolve().parent.parent / 'static' / 'editor' / 'js' / 'calvin_hardware.js'
        self.assertTrue(hw.exists(), f'No existe {hw}')
        hwc = hw.read_text(encoding='utf-8', errors='replace')
        self.assertIn('IO_TOOLBOX_DEFAULTS', hwc)
        self.assertIn('RGB_R', hwc)
