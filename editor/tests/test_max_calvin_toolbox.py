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
        self.assertIn('calvin_control_delay', block_types)
        self.assertIn('calvin_operator_add', block_types)
        self.assertIn('calvin_serial_begin', block_types)
        self.assertIn('calvin_io_digital_write', block_types)
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
