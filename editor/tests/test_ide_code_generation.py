"""
Tests para generación y validación de código del IDE.

Verifica que:
- El backend rechace código vacío
- El payload de compilación tenga estructura esperada
- Los helpers de validación funcionen correctamente

No depende de hardware real. No usa modo diagnóstico.
"""
from django.test import TestCase, Client
from django.urls import reverse
import json

from editor.ide_validation import (
    validate_compile_payload,
    validate_upload_payload,
    build_compile_payload,
    build_upload_payload,
    build_agent_compile_payload,
)


class CodeGenerationValidationTest(TestCase):
    """Tests de validación de generación de código."""

    def test_validate_compile_payload_empty_code_rejected(self):
        """Código vacío debe ser rechazado."""
        valid, err_code, err_msg = validate_compile_payload({'code': ''})
        self.assertFalse(valid)
        self.assertEqual(err_code, 'NO_CODE')
        self.assertIn('código', err_msg.lower())

    def test_validate_compile_payload_none_code_rejected(self):
        """Código None debe ser rechazado."""
        valid, err_code, _ = validate_compile_payload({'code': None})
        self.assertFalse(valid)
        self.assertEqual(err_code, 'NO_CODE')

    def test_validate_compile_payload_whitespace_only_rejected(self):
        """Código solo espacios debe ser rechazado."""
        valid, err_code, _ = validate_compile_payload({'code': '   \n\t  '})
        self.assertFalse(valid)
        self.assertEqual(err_code, 'NO_CODE')

    def test_validate_compile_payload_valid_accepted(self):
        """Código válido debe ser aceptado."""
        code = 'void setup() {} void loop() {}'
        valid, err_code, err_msg = validate_compile_payload({'code': code})
        self.assertTrue(valid)
        self.assertIsNone(err_code)
        self.assertIsNone(err_msg)

    def test_validate_compile_payload_sketch_ino_text_fallback(self):
        """sketch_ino_text como fallback de code."""
        code = 'void setup() { pinMode(13, OUTPUT); } void loop() {}'
        valid, _, _ = validate_compile_payload({'sketch_ino_text': code})
        self.assertTrue(valid)

    def test_validate_compile_payload_empty_dict_rejected(self):
        """Payload vacío (sin code) debe ser rechazado."""
        valid, err_code, _ = validate_compile_payload({})
        self.assertFalse(valid)
        self.assertEqual(err_code, 'NO_CODE')

    def test_validate_compile_payload_null_rejected(self):
        """Payload None debe ser rechazado."""
        valid, err_code, _ = validate_compile_payload(None)
        self.assertFalse(valid)
        self.assertEqual(err_code, 'NO_PAYLOAD')


class BuildPayloadTest(TestCase):
    """Tests de construcción de payloads."""

    def test_build_compile_payload_structure(self):
        """build_compile_payload produce estructura esperada."""
        code = 'void setup() {} void loop() {}'
        payload = build_compile_payload(code, 'arduino:avr:nano')
        self.assertEqual(payload['code'], code)
        self.assertEqual(payload['fqbn'], 'arduino:avr:nano')

    def test_build_compile_payload_default_fqbn(self):
        """FQBN por defecto es arduino:avr:uno."""
        payload = build_compile_payload('void setup() {} void loop() {}')
        self.assertEqual(payload['fqbn'], 'arduino:avr:uno')

    def test_build_upload_payload_structure(self):
        """build_upload_payload incluye code, port, board."""
        payload = build_upload_payload('code', 'COM3', 'arduino:avr:uno')
        self.assertEqual(payload['code'], 'code')
        self.assertEqual(payload['port'], 'COM3')
        self.assertIn('board', payload)
        self.assertIn('fqbn', payload)

    def test_build_agent_compile_payload_sketch_format(self):
        """Agent espera sketch.code, no code en raíz."""
        payload = build_agent_compile_payload('void setup() {} void loop() {}')
        self.assertIn('sketch', payload)
        self.assertIn('code', payload['sketch'])
        self.assertEqual(payload['sketch']['code'], 'void setup() {} void loop() {}')


class CodeStructureTest(TestCase):
    """Tests de estructura de código generado (lo que el backend espera)."""

    def test_valid_arduino_minimal_has_setup_loop(self):
        """Código Arduino válido mínima contiene setup y loop."""
        valid_codes = [
            'void setup() {} void loop() {}',
            'void setup() {\n  pinMode(13, OUTPUT);\n}\nvoid loop() {\n  digitalWrite(13, HIGH);\n}',
        ]
        for code in valid_codes:
            valid, _, _ = validate_compile_payload({'code': code})
            self.assertTrue(valid, f'Código debería ser válido: {code[:50]}...')
