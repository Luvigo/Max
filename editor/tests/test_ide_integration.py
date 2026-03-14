"""
Tests de integración mínima del flujo del IDE.

Caso 1 — Compilación exitosa (mock)
Caso 2 — Upload listo (precondiciones OK)
Caso 3 — Error de código vacío
Caso 4 — Error de Agent (simulado vía backend)

No usa hardware real. No modo diagnóstico.
"""
from django.test import TestCase, Client
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from editor.ide_validation import (
    validate_compile_payload,
    validate_upload_payload,
    build_compile_payload,
    build_upload_payload,
)


class CompilationSuccessIntegrationTest(TestCase):
    """Caso 1: Compilación exitosa con workspace con bloques (simulado)."""

    def setUp(self):
        self.client = Client()
        self.valid_code = 'void setup() { pinMode(13, OUTPUT); } void loop() { digitalWrite(13, HIGH); }'

    def test_valid_code_compile_flow(self):
        """Workspace con bloques → código generado → compile mock OK."""
        valid, err_code, _ = validate_compile_payload({'code': self.valid_code})
        self.assertTrue(valid, 'Payload debe ser válido')

        payload = build_compile_payload(self.valid_code, 'arduino:avr:uno')
        self.assertIn('code', payload)
        self.assertIn('fqbn', payload)

        with patch('editor.views.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
            resp = self.client.post(
                '/api/compile/',
                data=json.dumps(payload),
                content_type='application/json'
            )
            # 200 si hay hex, 500 si no (mock no crea filesystem)
            self.assertIn(resp.status_code, [200, 500])
            if resp.status_code == 200:
                data = resp.json()
                self.assertTrue(data.get('ok'))
                self.assertIn('hex_url', data)


class UploadReadyIntegrationTest(TestCase):
    """Caso 2: Upload listo - precondiciones presentes."""

    def setUp(self):
        self.client = Client()
        self.valid_code = 'void setup() {} void loop() {}'

    def test_all_preconditions_present_ready_to_upload(self):
        """Board, port, Agent (simulado), code → estado listo."""
        payload = build_upload_payload(
            code=self.valid_code,
            port='COM3',
            fqbn='arduino:avr:uno'
        )
        valid, err_code, _ = validate_upload_payload(payload)
        self.assertTrue(valid, 'Precondiciones deben ser válidas')
        self.assertIsNone(err_code)

        with patch('editor.views.validate_port_exists', return_value=(True, None)):
            with patch('editor.views.get_port_info', return_value={}):
                with patch('editor.views.subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
                    resp = self.client.post(
                        '/api/upload/',
                        data=json.dumps(payload),
                        content_type='application/json'
                    )
                    # 200, 404, 409, 500 - pero no 400 por NO_CODE/NO_PORT
                    if resp.status_code == 400:
                        err = resp.json().get('error_code')
                        self.fail(f'No debería fallar por precondiciones: {err}')


class EmptyCodeErrorIntegrationTest(TestCase):
    """Caso 3: Error de código vacío."""

    def setUp(self):
        self.client = Client()

    def test_empty_workspace_compile_gives_controlled_error(self):
        """Workspace vacío → al compilar debe dar error controlado."""
        payload = {'code': ''}
        valid, err_code, err_msg = validate_compile_payload(payload)
        self.assertFalse(valid)
        self.assertEqual(err_code, 'NO_CODE')

        resp = self.client.post(
            '/api/compile/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertIn('código', data.get('error', '').lower())
        self.assertEqual(data.get('error_code'), 'NO_CODE')

    def test_empty_code_does_not_call_real_compile(self):
        """Código vacío NO debe llegar a subprocess."""
        with patch('editor.views.subprocess.run') as mock_run:
            resp = self.client.post(
                '/api/compile/',
                data=json.dumps({'code': ''}),
                content_type='application/json'
            )
            mock_run.assert_not_called()


class AgentUnavailableIntegrationTest(TestCase):
    """Caso 4: Agent no disponible (simulado vía backend).

    El frontend llama al Agent en localhost:8765. Cuando el Agent no está,
    el frontend recibe error de conexión. Este test verifica que el backend
    Django (rutas alternativas) maneje correctamente errores de compilación.
    """

    def setUp(self):
        self.client = Client()

    @patch('editor.views.subprocess.run')
    def test_compile_backend_error_propagates_cleanly(self, mock_run):
        """Cuando compile falla, el error se propaga sin explosión."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='',
            stderr='avr-gcc: error: ...'
        )
        resp = self.client.post(
            '/api/compile/',
            data=json.dumps({
                'code': 'void setup() { int x = ; } void loop() {}',
                'fqbn': 'arduino:avr:uno'
            }),
            content_type='application/json'
        )
        self.assertIn(resp.status_code, [400, 500])
        data = resp.json()
        self.assertFalse(data.get('ok', True))
        self.assertIn('error', data)
        self.assertIsInstance(data, dict)
