"""
Tests unitarios para POST /upload del Agent.
- Routing por fqbn (avr vs esp32)
- FQBN inválido
- job_id no encontrado
- Retrocompat: code, hex_url

Ejecutar: pip install -r agent/requirements.txt && pytest agent/tests/test_upload.py -v
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    import flask
except ImportError:
    flask = None

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@unittest.skipIf(flask is None, "Flask no instalado. pip install -r agent/requirements.txt")
class TestUploadEndpoint(unittest.TestCase):
    """Tests para POST /upload - routing por fqbn"""

    def setUp(self):
        with patch.dict('sys.modules', {'serial': MagicMock(), 'serial.tools.list_ports': MagicMock()}):
            from agent.agent import app, _port_exists, _upload_job_store, _store_upload_job
            self.app = app
            self._port_exists = _port_exists
            self._upload_job_store = _upload_job_store
            self._store_upload_job = _store_upload_job
        self.client = self.app.test_client()

    def _upload_post(self, data):
        return self.client.post(
            '/upload',
            data=json.dumps(data),
            content_type='application/json'
        )

    @patch('agent.agent.ARDUINO_CLI', '/usr/bin/arduino-cli')
    @patch('agent.agent._port_exists')
    def test_upload_fqbn_invalido(self, mock_port_exists):
        """FQBN no registrado debe devolver 400."""
        mock_port_exists.return_value = True
        resp = self._upload_post({
            'fqbn': 'vendor:arch:board',
            'port': '/dev/ttyUSB0',
            'code': 'void setup() {} void loop() {}'
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get('ok'))
        self.assertIn('registry', data.get('error', '').lower())

    @patch('agent.agent.ARDUINO_CLI', '/usr/bin/arduino-cli')
    @patch('agent.agent._port_exists')
    def test_upload_routes_avr_by_fqbn(self, mock_port_exists):
        """FQBN arduino:avr:uno debe rutear a upload AVR."""
        mock_port_exists.return_value = True
        with patch('agent.agent._resolve_hex_for_upload') as mock_resolve:
            with patch('agent.agent._do_upload_avr') as mock_upload:
                mock_resolve.return_value = ('/tmp/fake.hex', None)
                mock_upload.return_value = (True, None, None)
                resp = self._upload_post({
                    'fqbn': 'arduino:avr:uno',
                    'port': '/dev/ttyUSB0',
                    'code': 'void setup() {} void loop() {}'
                })
                self.assertEqual(resp.status_code, 200)
                data = resp.get_json()
                self.assertTrue(data.get('ok'))
                self.assertEqual(data.get('family'), 'avr')
                self.assertEqual(data.get('fqbn'), 'arduino:avr:uno')
                mock_upload.assert_called_once()

    @patch('agent.agent.ARDUINO_CLI', '/usr/bin/arduino-cli')
    @patch('agent.agent._port_exists')
    def test_upload_routes_esp32_by_fqbn(self, mock_port_exists):
        """FQBN esp32:esp32:esp32 debe rutear a upload ESP32."""
        mock_port_exists.return_value = True
        with patch('agent.agent._resolve_bin_for_upload_esp32') as mock_resolve:
            with patch('agent.agent._do_upload_esp32') as mock_upload:
                with tempfile.TemporaryDirectory() as td:
                    (Path(td) / 'firmware.bin').write_bytes(b'\x00' * 64)
                    mock_resolve.return_value = (td, None)
                    mock_upload.return_value = (True, 'arduino-cli', None, None, [])
                    resp = self._upload_post({
                        'fqbn': 'esp32:esp32:esp32',
                        'port': '/dev/ttyUSB0',
                        'code': 'void setup() {} void loop() {}'
                    })
                    self.assertEqual(resp.status_code, 200)
                    data = resp.get_json()
                    self.assertTrue(data.get('ok'))
                    self.assertEqual(data.get('family'), 'esp32')
                    self.assertEqual(data.get('fqbn'), 'esp32:esp32:esp32')
                    mock_upload.assert_called_once()

    @patch('agent.agent.ARDUINO_CLI', '/usr/bin/arduino-cli')
    @patch('agent.agent._port_exists')
    def test_upload_job_id_not_found(self, mock_port_exists):
        """job_id inexistente debe devolver 400."""
        mock_port_exists.return_value = True
        resp = self._upload_post({
            'fqbn': 'arduino:avr:uno',
            'port': '/dev/ttyUSB0',
            'job_id': 'nonexistent123'
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get('ok'))
        self.assertEqual(data.get('error_code'), 'JOB_NOT_FOUND')

    @patch('agent.agent.ARDUINO_CLI', '/usr/bin/arduino-cli')
    @patch('agent.agent._port_exists')
    def test_upload_retrocompat_code(self, mock_port_exists):
        """Formato legacy { code, fqbn, port } debe funcionar (rutea a AVR)."""
        mock_port_exists.return_value = True
        with patch('agent.agent._resolve_hex_for_upload') as mock_resolve:
            with patch('agent.agent._do_upload_avr') as mock_upload:
                mock_resolve.return_value = ('/tmp/fake.hex', None)
                mock_upload.return_value = (True, None, None)
                resp = self._upload_post({
                    'code': 'void setup() {} void loop() {}',
                    'fqbn': 'arduino:avr:nano',
                    'port': 'COM3'
                })
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(resp.get_json().get('family'), 'avr')


if __name__ == '__main__':
    unittest.main()
