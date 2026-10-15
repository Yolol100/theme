"""Negative tests ensure automation cannot self-certify external/manual gates."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from sys import path as import_path
import_path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from validate_staging_acceptance import GATES, validate

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = json.loads((ROOT / 'docs/staging-acceptance.example.json').read_text())


class StagingReceiptTests(unittest.TestCase):
    def test_example_is_valid_but_not_approved(self):
        result = validate(EXAMPLE)
        self.assertEqual(result['status'], 'NO_GO')
        self.assertEqual(result['open_gates'], list(GATES))
        self.assertFalse(result['production_go_certified'])

    def test_missing_human_proof_cannot_pass(self):
        packet = copy.deepcopy(EXAMPLE)
        packet['staging_url'] = 'https://staging.example.test'
        packet['artifact']['commit_sha'] = 'a' * 40
        packet['gates']['wcag_em']['status'] = 'PASS'
        packet['gates']['wcag_em']['evidence'] = ['fake-evidence']
        result = validate(packet)
        self.assertEqual(result['status'], 'INVALID')
        self.assertTrue(any('named human reviewer' in e for e in result['errors']))
        self.assertTrue(any('screen reader' in e for e in result['errors']))

    def test_offline_order_is_not_payment_sandbox(self):
        packet = copy.deepcopy(EXAMPLE)
        packet['staging_url'] = 'https://staging.example.test'
        packet['artifact']['commit_sha'] = 'a' * 40
        packet['gates']['payment_sandbox'].update({
            'status': 'PASS', 'reviewer': 'QA reviewer',
            'evidence': ['receipt-12345'], 'observed_at': '2026-10-15T10:00:00Z',
            'provider': 'cheque', 'sandbox_order_reference': 'synthetic',
            'test_mode_confirmed': True, 'real_money_moved': False,
        })
        result = validate(packet)
        self.assertEqual(result['status'], 'INVALID')
        self.assertTrue(any('external provider' in e for e in result['errors']))

    def test_invalid_receipt_types_and_dates_never_crash(self):
        base = copy.deepcopy(EXAMPLE)
        base['staging_url'] = 'https://staging.example.test'
        base['artifact']['commit_sha'] = 'a' * 40
        gate = base['gates']['responsive_devices']
        gate.update({
            'status': 'PASS', 'reviewer': 'Human QA reviewer',
            'observed_at': '2026-10-15T10:00:00Z', 'evidence': ['report-123456'],
            'widths_checked': [320, 375, 390, 768, 1024, 1440, 1920],
            'actual_zoom_200_percent': True,
        })
        cases = (
            (('gates', 'responsive_devices', 'observed_at'), '2026-99-99T88:77:66Z'),
            (('staging_url',), 'https://bad host.example.test'),
            (('artifact', 'theme_sha256'), 8),
            (('gates', 'responsive_devices', 'widths_checked'), None),
            (('gates', 'responsive_devices', 'status'), ['PASS']),
        )
        for keypath, value in cases:
            with self.subTest(keypath=keypath):
                packet = copy.deepcopy(base)
                target = packet
                for key in keypath[:-1]:
                    target = target[key]
                target[keypath[-1]] = value
                result = validate(packet)
                self.assertEqual(result['status'], 'INVALID')
                self.assertTrue(result['errors'])
                self.assertFalse(result['production_go_certified'])

    def test_zip_digest_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            zip_file = Path(tmp) / 'sample.zip'
            zip_file.write_bytes(b'not the approved ZIP')
            result = validate(EXAMPLE, zip_file)
        self.assertEqual(result['status'], 'INVALID')
        self.assertTrue(any('exact tested ZIP' in e for e in result['errors']))

    def test_all_checkboxes_do_not_automatically_certify_production(self):
        packet = copy.deepcopy(EXAMPLE)
        packet['staging_url'] = 'https://staging.example.test'
        packet['artifact']['commit_sha'] = 'a' * 40
        common = {'status': 'PASS', 'reviewer': 'Human QA reviewer',
                  'observed_at': '2026-10-15T10:00:00Z', 'evidence': ['test-evidence-123']}
        for entry in packet['gates'].values():
            entry.update(common)
        packet['gates']['gutenberg_ui'].update({
            'admin_editor_roles': True, 'site_editor_roundtrip': True, 'frontend_comparison': True})
        packet['gates']['wcag_em'].update({
            'keyboard_tested': True, 'screenreader_tested': True,
            'sample': ['home', 'editor', 'checkout']})
        packet['gates']['responsive_devices'].update({
            'actual_zoom_200_percent': True,
            'widths_checked': [320, 375, 390, 768, 1024, 1440, 1920]})
        packet['gates']['payment_sandbox'].update({
            'provider': 'Test gateway', 'sandbox_order_reference': 'sandbox-123',
            'test_mode_confirmed': True, 'real_money_moved': False})
        packet['gates']['hosting_rollback'].update({
            'hosting_backup_restored': True, 'database_and_uploads_verified': True,
            'post_restore_smoke_pass': True})
        result = validate(packet)
        self.assertEqual(result['status'], 'AWAITING_INDEPENDENT_SIGNOFF')
        self.assertFalse(result['production_go_certified'])


if __name__ == '__main__':
    unittest.main()
