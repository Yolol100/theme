"""Validate staging receipt fields and the installation archive's hash.

This checks the record, not the truth of human observations or provider results.
A valid receipt still requires independent release approval.
"""
import argparse
from datetime import datetime, timedelta
import ipaddress
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

GATES = ('gutenberg_ui', 'wcag_em', 'responsive_devices', 'payment_sandbox',
         'hosting_rollback', 'owner_signoff')
STATUSES = frozenset(('PASS', 'FAIL', 'PARTIAL', 'NOT_RUN', 'BLOCKED', 'N/A'))
SHA256 = re.compile(r'^[0-9a-f]{64}$')
COMMIT = re.compile(r'^[0-9a-f]{40}$')
STAMP = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})\Z')
HOST_LABEL = re.compile(r'^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$')


def valid_timestamp(value):
    if not isinstance(value, str) or not STAMP.fullmatch(value):
        return False
    try:
        moment = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return (moment.tzinfo is not None and moment.utcoffset() is not None
                and abs(moment.utcoffset()) <= timedelta(hours=14))
    except ValueError:
        return False


def valid_staging_url(value):
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        return False
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        if (parsed.scheme != 'https' or not host or parsed.username is not None or
            parsed.password is not None or parsed.port == 0 or parsed.fragment):
            return False
        try:
            ipaddress.ip_address(host)
            return True
        except ValueError:
            labels = host.rstrip('.').split('.')
            return (len(host) <= 253 and len(labels) >= 2 and
                    all(HOST_LABEL.fullmatch(label) for label in labels))
    except ValueError:
        return False


def validate(packet, zip_file=None, expected_commit=None):
    errors = []
    open_gates = []
    if not isinstance(packet, dict):
        return {'status': 'INVALID', 'errors': ['Receipt must be an object'], 'open_gates': list(GATES)}
    if packet.get('schema_version') != 1:
        errors.append('schema_version must be 1')
    artifact = packet.get('artifact', {})
    if not isinstance(artifact, dict):
        artifact = {}
        errors.append('artifact must be an object')
    digest = artifact.get('theme_sha256', '')
    commit = artifact.get('commit_sha', '')
    if not isinstance(digest, str) or (digest and not SHA256.fullmatch(digest)):
        errors.append('artifact.theme_sha256 must be a SHA-256 hex digest')
    if not isinstance(commit, str) or (commit and not COMMIT.fullmatch(commit)):
        errors.append('artifact.commit_sha must be a complete commit SHA')
    if expected_commit and commit != expected_commit:
        errors.append('Receipt commit does not equal expected commit')
    if zip_file is not None:
        actual = hashlib.sha256(Path(zip_file).read_bytes()).hexdigest()
        if digest != actual:
            errors.append('Receipt theme_sha256 does not match exact tested ZIP')
    url = packet.get('staging_url', '')
    if url and not valid_staging_url(url):
        errors.append('staging_url must be HTTPS with a valid hostname, without credentials')
    elif not isinstance(url, str):
        errors.append('staging_url must be a string')
    gates = packet.get('gates')
    if not isinstance(gates, dict) or set(gates) != set(GATES):
        errors.append('gates must contain exactly the six required acceptance categories')
        gates = gates if isinstance(gates, dict) else {}
    for name in GATES:
        review = gates.get(name, {})
        if (not isinstance(review, dict) or
            not isinstance(review.get('status'), str) or review['status'] not in STATUSES):
            errors.append(f'{name}: invalid or missing status')
            open_gates.append(name)
            continue
        if review['status'] != 'PASS':
            open_gates.append(name)
            continue
        if not (url and digest and commit):
            errors.append(f'{name}: PASS requires staging URL, commit and exact ZIP SHA')
        reviewer = review.get('reviewer')
        if not isinstance(reviewer, str) or len(reviewer.strip()) < 3:
            errors.append(f'{name}: PASS requires a named human reviewer')
        evidence = review.get('evidence')
        if not (isinstance(evidence, list) and evidence and
                all(isinstance(x, str) and len(x.strip()) >= 8 for x in evidence)):
            errors.append(f'{name}: PASS requires non-empty traceable evidence IDs')
        if not valid_timestamp(review.get('observed_at')):
            errors.append(f'{name}: PASS requires an ISO 8601 timestamp with timezone')
        if name == 'gutenberg_ui' and not all(review.get(x) is True for x in (
            'admin_editor_roles', 'site_editor_roundtrip', 'frontend_comparison'
        )):
            errors.append('gutenberg_ui: real admin/editor, Site Editor and frontend roundtrips required')
        if name == 'wcag_em':
            if review.get('methodology') != 'WCAG-EM 2.0' or review.get('target') != 'WCAG 2.2 AA':
                errors.append('wcag_em: use WCAG-EM 2.0 for WCAG 2.2 AA')
            if not (review.get('keyboard_tested') is True and
                    review.get('screenreader_tested') is True and
                    isinstance(review.get('sample'), list) and len(review['sample']) >= 3):
                errors.append('wcag_em: representative sample, keyboard and screen reader required')
        if name == 'responsive_devices':
            widths = review.get('widths_checked')
            if not (review.get('actual_zoom_200_percent') is True and
                    isinstance(widths, list) and all(type(x) is int for x in widths) and
                    set(widths) >= {320, 375, 390, 768, 1024, 1440, 1920}):
                errors.append('responsive_devices: all widths and real 200% browser zoom required')
        if name == 'payment_sandbox':
            if (not review.get('provider') or not review.get('sandbox_order_reference') or
                review.get('test_mode_confirmed') is not True or
                review.get('real_money_moved') is not False or
                str(review.get('provider')).lower() in ('cheque', 'cod', 'offline')):
                errors.append('payment_sandbox: external provider test mode and genuine test order required; no real funds')
        if name == 'hosting_rollback' and not (
            review.get('hosting_backup_restored') is True and
            review.get('database_and_uploads_verified') is True and
            review.get('post_restore_smoke_pass') is True
        ):
            errors.append('hosting_rollback: real host backup, DB/uploads and post-restore checks required')
    status = 'INVALID' if errors else ('AWAITING_INDEPENDENT_SIGNOFF' if not open_gates else 'NO_GO')
    return {
        'status': status, 'open_gates': open_gates, 'errors': errors,
        'production_go_certified': False,
        'limitation': 'Receipt validation cannot authenticate human observations, third-party payments or host operations',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipt', type=Path)
    parser.add_argument('--zip', dest='zip_file', type=Path)
    parser.add_argument('--expected-commit')
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    result = validate(json.loads(args.receipt.read_text()), args.zip_file, args.expected_commit)
    print(json.dumps(result, indent=2))
    if result['errors'] or (args.require_complete and result['status'] != 'AWAITING_INDEPENDENT_SIGNOFF'):
        sys.exit(2)


if __name__ == '__main__':
    main()
