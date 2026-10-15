"""Source-level guards for optional ACF testing; runtime assertions live in Docker."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AcfContractTests(unittest.TestCase):
    def test_acf_stays_outside_the_theme(self):
        theme = ROOT / 'theme/webactueel-starter'
        self.assertEqual(len([p for p in theme.rglob('*') if p.is_file()]), 12)
        self.assertFalse(any('acf' in p.name.lower() for p in theme.rglob('*')))
        self.assertFalse(list(theme.rglob('*.php')))
        package = (ROOT / 'scripts/package.py').read_text()
        for path in ('docs/ARCHITECTURE.md', 'tests/runtime/acf_smoke.php',
                     'tests/runtime/acf_smoke.sh', 'tests/test_acf_contract.py'):
            self.assertIn(path, package)
        self.assertNotIn('OPTIONAL_SCAFFOLD', package)

    def test_official_plugin_archive_and_digest_are_pinned(self):
        script = (ROOT / 'tests/runtime/acf_smoke.sh').read_text()
        self.assertIn('AdvancedCustomFields/acf/releases/download/6.8.10/', script)
        self.assertIn('2396bf0ddf28c263bae4a31115162c78608520503404f2bd075e1bfcf37bcb56', script)
        self.assertLess(script.index('sha256sum --check -'), script.index('wp plugin install'))
        self.assertNotIn('wp plugin install advanced-custom-fields', script)
        self.assertIn("'acf_pro_blocks_and_datastore': 'NOT_RUN'", script)
        self.assertIn('check_frontend inactive', script)
        self.assertIn('wp plugin delete advanced-custom-fields', script)
        runner = (ROOT / 'tests/runtime/run.sh').read_text()
        self.assertLess(runner.index('python3 tests/runtime/axe_audit.py'),
                        runner.index('bash tests/runtime/acf_smoke.sh'))

    def test_page_scopes_and_negative_field_access_are_exercised(self):
        fixture = (ROOT / 'tests/runtime/acf_smoke.php').read_text()
        self.assertIn("'http://localhost:8080' !== get_option( 'home' )", fixture)
        for token in ('acf_update_field_group', 'acf_update_field', 'acf_get_field_groups',
                      'get_field', 'update_field', 'acf_delete_field_group'):
            self.assertIn(token, fixture)
        self.assertIn("'summary' => 1, 'internal' => 0", fixture)
        self.assertIn("'param' => 'page'", fixture)
        self.assertIn('CI restricted value must not render', fixture)

    def test_scenario_ids_and_english_acceptance_text(self):
        manifest = json.loads((ROOT / 'docs/77-scenarios.json').read_text())
        self.assertEqual([case['id'] for case in manifest['scenarios']], list(range(1, 78)))
        self.assertEqual(manifest['scenario_count'], 77)
        for case in manifest['scenarios']:
            self.assertFalse(re.search(r'\b(toont|geen|juiste|gecontroleerd|behouden|inhoud|ontbreken)\b',
                                       case['acceptance_assertion'], re.I))
            self.assertTrue(case['acceptance_assertion'].isascii())

    def test_theme_switch_uses_a_compatible_installed_theme(self):
        script = (ROOT / 'tests/runtime/acf_smoke.sh').read_text()
        self.assertIn('is_wp_version_compatible', script)
        self.assertIn('is_php_version_compatible', script)
        self.assertIn('$theme->errors()', script)
        self.assertIn('No compatible alternate theme is installed.', script)
        self.assertIn("'alternate_theme': os.environ['ACF_SWITCH_THEME']", script)
        self.assertNotIn('wp theme list --status=inactive --field=name', script)
