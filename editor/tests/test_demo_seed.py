"""
Tests para seed de datos demo.

- seed_demo_data command rechaza en producción.
- seed_demo_data requiere SEED_DEMO_DATA=1 para ejecutar.
"""
from django.test import TestCase
from unittest.mock import patch
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO


class SeedDemoDataCommandTest(TestCase):
    """Tests para el comando seed_demo_data"""

    def test_refuses_in_production(self):
        """En ENV=production el comando rechaza con CommandError"""
        with patch.dict('os.environ', {'ENV': 'production', 'SEED_DEMO_DATA': '1'}, clear=False):
            with self.assertRaises(CommandError):
                call_command('seed_demo_data')

    def test_refuses_without_seed_var(self):
        """Sin SEED_DEMO_DATA=1 el comando rechaza"""
        with patch.dict('os.environ', {'RENDER': '', 'ENV': ''}, clear=False):
            import os
            os.environ.pop('SEED_DEMO_DATA', None)
            with self.assertRaises(CommandError):
                call_command('seed_demo_data')

    def test_runs_with_opt_in(self):
        """Con SEED_DEMO_DATA=1 en dev, el comando ejecuta (idempotente). Verificación manual: SEED_DEMO_DATA=1 python manage.py seed_demo_data"""
        from django.db import connection
        # Skip en SQLite: migrations UUID pueden causar datatype mismatch
        if connection.vendor == 'sqlite':
            self.skipTest('seed_demo_data test skip on SQLite (UUID compatibility)')
        with patch.dict('os.environ', {'RENDER': '', 'ENV': '', 'SEED_DEMO_DATA': '1'}, clear=False):
            out = StringIO()
            call_command('seed_demo_data', stdout=out)
            self.assertIn('[DEMO_SEED]', out.getvalue())
