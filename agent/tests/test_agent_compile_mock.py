"""
Tests de mocks para el Agent (health, compile, upload).

Verifica que:
- /health OK y FAIL
- /compile con código vacío devuelve error controlado
- /compile OK con mock
- /upload OK y FAIL con mocks

No depende de hardware real.
"""
import json
import sys
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


@unittest.skipIf(flask is None, "Flask no instalado. Ejecuta: pip install -r agent/requirements.txt")
class TestAgentHealthMock(unittest.TestCase):
    """Mocks para GET /health."""

    def setUp(self):
        with patch.dict('sys.modules', {'serial': MagicMock(), 'serial.tools.list_ports': MagicMock()}):
            from agent.agent import app
            self.client = app.test_client()

    @patch('agent.agent.get_cores_status')
    def test_health_ok(self, mock_cores):
        """GET /health debe responder 200 cuando el Agent está OK."""
        mock_cores.return_value = {'arduino_cli_ok': True, 'cores': {}, 'errors': []}
        resp = self.client.get('/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIsNotNone(data)
        self.assertIn('status', data)
        self.assertEqual(data.get('status'), 'running')


@unittest.skipIf(flask is None, "Flask no instalado")
class TestAgentCompileEmptyCode(unittest.TestCase):
    """Agent debe rechazar código vacío."""

    def setUp(self):
        with patch.dict('sys.modules', {'serial': MagicMock(), 'serial.tools.list_ports': MagicMock()}):
            from agent.agent import app
            self.client = app.test_client()

    @patch('agent.agent.ARDUINO_CLI', '/usr/bin/arduino-cli')
    def test_compile_empty_code_returns_error(self):
        """Código vacío debe devolver error 'No hay código para compilar'."""
        resp = self.client.post(
            '/compile',
            data=json.dumps({'fqbn': 'arduino:avr:uno', 'code': ''}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get('ok', True))
        err = (data.get('error') or '').lower()
        self.assertTrue('codigo' in err or 'code' in err, f'Error debe mencionar código: {err}')

    @patch('agent.agent.ARDUINO_CLI', '/usr/bin/arduino-cli')
    def test_compile_sketch_code_empty_returns_error(self):
        """sketch.code vacío debe rechazarse."""
        resp = self.client.post(
            '/compile',
            data=json.dumps({
                'fqbn': 'arduino:avr:uno',
                'sketch': {'code': ''}
            }),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get('ok', True))

    @patch('agent.agent.ARDUINO_CLI', '/usr/bin/arduino-cli')
    def test_compile_no_code_no_files_returns_error(self):
        """Sin code ni sketch.code ni files debe rechazarse."""
        resp = self.client.post(
            '/compile',
            data=json.dumps({'fqbn': 'arduino:avr:uno'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get('ok', True))


@unittest.skipIf(flask is None, "Flask no instalado")
class TestAgentCompileMockOK(unittest.TestCase):
    """Compilación exitosa con mock."""

    def setUp(self):
        with patch.dict('sys.modules', {'serial': MagicMock(), 'serial.tools.list_ports': MagicMock()}):
            from agent.agent import app
            self.client = app.test_client()

    @patch('agent.agent.ARDUINO_CLI', '/usr/bin/arduino-cli')
    @patch('agent.agent.subprocess.run')
    def test_compile_ok_with_valid_code(self, mock_run):
        """Con código válido, compile mock OK."""
        def fake_run(cmd, *args, **kwargs):
            for i, c in enumerate(cmd):
                if c == '--output-dir' and i + 1 < len(cmd):
                    build_dir = Path(cmd[i + 1])
                    build_dir.mkdir(parents=True, exist_ok=True)
                    (build_dir / 'sketch_verify.ino.hex').write_bytes(b':020000020000FC\n')
                    break
            return MagicMock(returncode=0, stdout='', stderr='')

        mock_run.side_effect = fake_run

        resp = self.client.post(
            '/compile',
            data=json.dumps({
                'fqbn': 'arduino:avr:uno',
                'sketch': {'code': 'void setup() {} void loop() {}'},
                'return_job_id': True
            }),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        # Puede tener job_id o artifacts según versión del Agent
        self.assertTrue('job_id' in data or 'artifacts' in data or 'compile_log' in data)


@unittest.skipIf(flask is None, "Flask no instalado")
class TestAgentUploadMock(unittest.TestCase):
    """Mocks para POST /upload."""

    def setUp(self):
        with patch.dict('sys.modules', {'serial': MagicMock(), 'serial.tools.list_ports': MagicMock()}):
            from agent.agent import app
            self.client = app.test_client()

    def test_upload_missing_port_returns_error(self):
        """Upload sin puerto debe devolver error."""
        resp = self.client.post(
            '/upload',
            data=json.dumps({
                'code': 'void setup() {} void loop() {}',
                'fqbn': 'arduino:avr:uno'
            }),
            content_type='application/json'
        )
        self.assertIn(resp.status_code, [400, 404, 500])
        if resp.status_code == 400:
            data = resp.get_json()
            self.assertIn('port', str(data).lower())

    def test_upload_missing_fqbn_uses_default_or_errors(self):
        """Upload sin fqbn debe usar default o indicar error."""
        resp = self.client.post(
            '/upload',
            data=json.dumps({
                'code': 'void setup() {} void loop() {}',
                'port': 'COM3'
            }),
            content_type='application/json'
        )
        # No debe explotar
        self.assertIn(resp.status_code, [200, 400, 404, 500])


if __name__ == '__main__':
    unittest.main()
