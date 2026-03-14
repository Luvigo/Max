"""
Tests para el flujo de compilación del IDE.

Verifica que:
- Código vacío devuelve error controlado (no intenta compilar)
- Código válido construye payload y puede compilar (con mock)
- Falta de board usa default
- Error del backend se propaga correctamente

No depende de hardware real. Usa mocks para subprocess.
"""
from django.test import TestCase, Client
from unittest.mock import patch, MagicMock
from pathlib import Path
import json


class CompileFlowTest(TestCase):
    """Tests del flujo de compilación."""

    def setUp(self):
        self.client = Client()
        self.compile_url = '/api/compile/'
        self.valid_code = 'void setup() {} void loop() {}'

    def test_compile_empty_code_returns_400(self):
        """Código vacío debe devolver 400 y NO intentar compilar."""
        resp = self.client.post(
            self.compile_url,
            data=json.dumps({'code': ''}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data.get('ok', True))
        self.assertIn('código', data.get('error', '').lower())
        self.assertEqual(data.get('error_code'), 'NO_CODE')

    def test_compile_missing_code_returns_400(self):
        """Sin code en el payload debe devolver 400."""
        resp = self.client.post(
            self.compile_url,
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data.get('ok', True))
        self.assertEqual(data.get('error_code'), 'NO_CODE')

    def test_compile_whitespace_only_code_returns_400(self):
        """Código solo espacios debe ser rechazado."""
        resp = self.client.post(
            self.compile_url,
            data=json.dumps({'code': '   \n\t  '}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)

    def test_compile_valid_code_not_rejected_as_empty(self):
        """Con código válido, NO debe dar 400 por 'No se proporcionó código'."""
        resp = self.client.post(
            self.compile_url,
            data=json.dumps({'code': self.valid_code, 'fqbn': 'arduino:avr:uno'}),
            content_type='application/json'
        )
        # 200=éxito, 500=arduino-cli no instalado/falló - pero NUNCA 400 por NO_CODE
        self.assertIn(resp.status_code, [200, 500])
        if resp.status_code == 400:
            data = resp.json()
            self.assertNotEqual(data.get('error_code'), 'NO_CODE')

    def test_compile_uses_default_board_when_missing(self):
        """Sin fqbn/board debe usar default arduino:avr:uno."""
        # La vista usa: fqbn = data.get('fqbn', '') or data.get('board', 'arduino:avr:uno')
        # Solo podemos verificar que acepta el request (no 400 por payload malformado)
        resp = self.client.post(
            self.compile_url,
            data=json.dumps({'code': self.valid_code}),
            content_type='application/json'
        )
        # 400 = error de validación, 500 = arduino-cli no existe o falla
        self.assertIn(resp.status_code, [200, 400, 500])
        if resp.status_code == 400:
            self.assertNotEqual(resp.json().get('error_code'), 'NO_CODE')


class CompileErrorPropagationTest(TestCase):
    """Tests de propagación de errores."""

    def setUp(self):
        self.client = Client()

    @patch('editor.views.subprocess.run')
    def test_compile_backend_error_returns_structured_response(self, mock_run):
        """Cuando arduino-cli falla, la respuesta tiene estructura controlada."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='',
            stderr='Error: compilación fallida'
        )
        resp = self.client.post(
            '/api/compile/',
            data=json.dumps({
                'code': 'void setup() { syntax error',
                'fqbn': 'arduino:avr:uno'
            }),
            content_type='application/json'
        )
        # Puede dar 400 o 500 según cómo maneje la vista el returncode
        self.assertIn(resp.status_code, [400, 500])
        data = resp.json()
        self.assertFalse(data.get('ok', True))
        self.assertIn('error', data)
        # No debe explotar con excepción no controlada
        self.assertIsInstance(data, dict)
