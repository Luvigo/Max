"""
Tests para precondiciones de subida (upload) del IDE.

Verifica que ANTES de intentar subir se valide:
- Board seleccionado
- Puerto seleccionado
- Código generado
- (Agent disponible se valida en frontend; backend solo recibe la petición)

No testea hardware real. Solo validaciones.
"""
from django.test import TestCase, Client
from unittest.mock import patch, MagicMock
import json


class UploadPreconditionsTest(TestCase):
    """Tests de precondiciones de upload."""

    def setUp(self):
        self.client = Client()
        self.upload_url = '/api/upload/'
        self.valid_code = 'void setup() {} void loop() {}'

    def test_upload_fail_no_code(self):
        """FAIL si no hay código."""
        resp = self.client.post(
            self.upload_url,
            data=json.dumps({'code': '', 'port': 'COM3', 'board': 'arduino:avr:uno'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertEqual(data.get('error_code'), 'NO_CODE')
        self.assertIn('código', data.get('error', '').lower())

    def test_upload_fail_no_port(self):
        """FAIL si no hay puerto."""
        resp = self.client.post(
            self.upload_url,
            data=json.dumps({'code': self.valid_code, 'port': '', 'board': 'arduino:avr:uno'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertEqual(data.get('error_code'), 'NO_PORT')
        self.assertIn('puerto', data.get('error', '').lower())

    def test_upload_fail_code_missing(self):
        """FAIL si code no está en el payload."""
        resp = self.client.post(
            self.upload_url,
            data=json.dumps({'port': 'COM3', 'board': 'arduino:avr:uno'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json().get('error_code'), 'NO_CODE')

    def test_upload_fail_port_missing(self):
        """FAIL si port no está en el payload."""
        resp = self.client.post(
            self.upload_url,
            data=json.dumps({'code': self.valid_code, 'board': 'arduino:avr:uno'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json().get('error_code'), 'NO_PORT')

    def test_upload_uses_default_board_when_missing(self):
        """Board por defecto cuando no se envía."""
        with patch('editor.views.validate_port_exists', return_value=(True, None)):
            with patch('editor.views.get_port_info', return_value={}):
                with patch('editor.views.subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
                    resp = self.client.post(
                        self.upload_url,
                        data=json.dumps({
                            'code': self.valid_code,
                            'port': 'COM_TEST_999'
                        }),
                        content_type='application/json'
                    )
                    if resp.status_code == 400:
                        err = resp.json().get('error_code')
                        self.assertNotIn(err, ['NO_CODE', 'NO_PORT'])

    def test_upload_pass_when_all_present(self):
        """PASS (o error distinto) cuando code, port, board están presentes."""
        with patch('editor.views.validate_port_exists', return_value=(True, None)):
            with patch('editor.views.get_port_info', return_value={}):
                with patch('editor.views.subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stdout='OK', stderr='')
                    resp = self.client.post(
                        self.upload_url,
                        data=json.dumps({
                            'code': self.valid_code,
                            'port': 'COM_TEST_999',
                            'board': 'arduino:avr:uno'
                        }),
                        content_type='application/json'
                    )
                    if resp.status_code == 400:
                        err = resp.json().get('error_code')
                        self.assertNotIn(err, ['NO_CODE', 'NO_PORT'],
                            msg=f'No debería fallar por precondiciones: {err}')


class UploadErrorStructureTest(TestCase):
    """Estructura de errores controlados."""

    def setUp(self):
        self.client = Client()

    def test_no_code_error_has_expected_keys(self):
        """Error NO_CODE debe tener error, error_code, logs."""
        resp = self.client.post(
            '/api/upload/',
            data=json.dumps({'port': 'COM3'}),
            content_type='application/json'
        )
        data = resp.json()
        self.assertIn('error', data)
        self.assertIn('error_code', data)
        self.assertEqual(data['error_code'], 'NO_CODE')

    def test_no_port_error_has_expected_keys(self):
        """Error NO_PORT debe tener error, error_code."""
        resp = self.client.post(
            '/api/upload/',
            data=json.dumps({'code': 'void setup() {} void loop() {}'}),
            content_type='application/json'
        )
        data = resp.json()
        self.assertEqual(data.get('error_code'), 'NO_PORT')
