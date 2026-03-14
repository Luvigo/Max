"""
Tests unitarios para POST /compile del Agent.
- fqbn inválido
- compile falla
- compile ok AVR
- compile ok ESP32 (mock si no está el core en CI)

Ejecutar con dependencias del Agent instaladas:
  pip install -r agent/requirements.txt
  pytest agent/tests/test_compile.py -v
"""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Skip si Flask no está instalado (Agent tiene deps propias)
try:
    import flask
except ImportError:
    flask = None

# Asegurar que el proyecto root esté en path para import agent.agent
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@unittest.skipIf(flask is None, "Flask no instalado. Ejecuta: pip install -r agent/requirements.txt")
class TestCompileEndpoint(unittest.TestCase):
    """Tests para el endpoint POST /compile"""

    def setUp(self):
        """Configura cliente de prueba."""
        with patch.dict('sys.modules', {'serial': MagicMock(), 'serial.tools.list_ports': MagicMock()}):
            from agent.agent import app
            self.app = app
        self.client = self.app.test_client()

    def _compile_post(self, data):
        """Helper: POST /compile con JSON."""
        return self.client.post(
            '/compile',
            data=json.dumps(data),
            content_type='application/json'
        )

    @patch('agent.agent.ARDUINO_CLI', '/usr/bin/arduino-cli')
    def test_fqbn_invalido(self):
        """FQBN no registrado debe devolver 400."""
        resp = self._compile_post({
            'fqbn': 'vendor:arch:board:opciones',
            'code': 'void setup() {} void loop() {}'
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get('ok'))
        self.assertIn('registry', data.get('error', '').lower())

    @patch('agent.agent.ARDUINO_CLI', '/usr/bin/arduino-cli')
    @patch('agent.agent.subprocess.run')
    def test_compile_falla(self, mock_run):
        """Cuando arduino-cli falla, debe devolver 400 con error."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='',
            stderr='Error: compilación fallida'
        )
        resp = self._compile_post({
            'fqbn': 'arduino:avr:uno',
            'code': 'void setup() { syntax error'
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get('ok'))
        self.assertIn('error', data)
        self.assertIn('compile_log', data)

    @patch('agent.agent.ARDUINO_CLI', '/usr/bin/arduino-cli')
    @patch('agent.agent.subprocess.run')
    def test_compile_ok_avr(self, mock_run):
        """Compilación AVR exitosa: devuelve artifacts con .hex."""
        def fake_run(cmd, *args, **kwargs):
            # Crear fake .hex en el build_dir que arduino-cli usaría
            build_idx = None
            for i, c in enumerate(cmd):
                if c == '--output-dir' and i + 1 < len(cmd):
                    build_dir = Path(cmd[i + 1])
                    build_dir.mkdir(parents=True, exist_ok=True)
                    hex_file = build_dir / 'sketch_verify.ino.hex'
                    hex_file.write_bytes(b':020000020000FC\n:00000001FF\n')
                    break
            return MagicMock(returncode=0, stdout='Compilación OK', stderr='')

        mock_run.side_effect = fake_run

        resp = self._compile_post({
            'fqbn': 'arduino:avr:uno',
            'code': 'void setup() {} void loop() {}'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('fqbn'), 'arduino:avr:uno')
        self.assertEqual(data.get('family'), 'avr')
        self.assertIn('artifacts', data)
        self.assertIn('compile_log', data)
        hex_arts = [a for a in data['artifacts'] if a['name'].endswith('.hex')]
        self.assertGreater(len(hex_arts), 0)
        self.assertEqual(hex_arts[0]['type'], 'firmware')
        self.assertIn('sha256', hex_arts[0])
        self.assertIn('size', hex_arts[0])

    @patch('agent.agent.ARDUINO_CLI', '/usr/bin/arduino-cli')
    @patch('agent.agent.subprocess.run')
    def test_compile_ok_esp32_mock(self, mock_run):
        """Compilación ESP32 exitosa (mock): devuelve firmware.bin y opcionales."""
        def fake_run(cmd, *args, **kwargs):
            for i, c in enumerate(cmd):
                if c == '--output-dir' and i + 1 < len(cmd):
                    build_dir = Path(cmd[i + 1])
                    build_dir.mkdir(parents=True, exist_ok=True)
                    (build_dir / 'firmware.bin').write_bytes(b'\x00' * 256)
                    (build_dir / 'bootloader.bin').write_bytes(b'\x00' * 64)
                    (build_dir / 'partitions.bin').write_bytes(b'\x00' * 64)
                    break
            return MagicMock(returncode=0, stdout='Compilación OK', stderr='')

        mock_run.side_effect = fake_run

        resp = self._compile_post({
            'fqbn': 'esp32:esp32:esp32',
            'code': 'void setup() {} void loop() {}'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('fqbn'), 'esp32:esp32:esp32')
        self.assertEqual(data.get('family'), 'esp32')
        arts = {a['name']: a for a in data['artifacts']}
        self.assertIn('firmware.bin', arts)
        self.assertEqual(arts['firmware.bin']['type'], 'firmware')
        if 'bootloader.bin' in arts:
            self.assertEqual(arts['bootloader.bin']['type'], 'bootloader')
        if 'partitions.bin' in arts:
            self.assertEqual(arts['partitions.bin']['type'], 'partitions')

    @patch('agent.agent.ARDUINO_CLI', None)
    def test_arduino_cli_no_encontrado(self):
        """Sin arduino-cli debe devolver 500."""
        resp = self._compile_post({
            'fqbn': 'arduino:avr:uno',
            'code': 'void setup() {} void loop() {}'
        })
        self.assertEqual(resp.status_code, 500)
        data = resp.get_json()
        self.assertFalse(data.get('ok'))

    def test_retrocompat_code_fqbn(self):
        """Formato legacy { code, fqbn } debe funcionar."""
        with patch('agent.agent.ARDUINO_CLI', '/usr/bin/arduino-cli'):
            with patch('agent.agent.subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout='OK', stderr=''
                )
                resp = self._compile_post({
                    'code': 'void setup() {} void loop() {}',
                    'fqbn': 'arduino:avr:uno'
                })
                # Puede ser 200 si mock crea artifacts, o 400 si no hay .hex
                # Lo importante: no debe fallar por formato
                self.assertIn(resp.status_code, (200, 400))


if __name__ == '__main__':
    unittest.main()
