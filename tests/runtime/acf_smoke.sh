#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
compose=(docker compose -f tests/runtime/compose.yaml)
wp() { "${compose[@]}" run --rm -T cli wp "$@"; }

# This runner uses only the existing disposable Docker site.
[ "$(wp option get home | tr -d '\r')" = 'http://localhost:8080' ]
[ "$(wp option get stylesheet | tr -d '\r')" = 'webactueel-starter' ]
if wp plugin is-installed advanced-custom-fields; then
  echo 'ACF already exists; use a fresh disposable site for this test.' >&2
  exit 1
fi
archive=dist/.acf-test-6.8.10.zip
trap 'rm -f "$archive"' EXIT
mkdir -p reports
curl --fail --silent --show-error --location --retry 2 \
  --proto '=https' --proto-redir '=https' --tlsv1.2 --connect-timeout 20 --max-time 120 \
  https://github.com/AdvancedCustomFields/acf/releases/download/6.8.10/advanced-custom-fields-6.8.10.zip \
  --output "$archive"
printf '%s  %s\n' 2396bf0ddf28c263bae4a31115162c78608520503404f2bd075e1bfcf37bcb56 "$archive" | sha256sum --check -
wp plugin install /workspace/dist/.acf-test-6.8.10.zip --activate
wp eval-file /workspace/acf_smoke.php seed > reports/acf-fixture.json
wp eval-file /workspace/acf_smoke.php verify > reports/acf-fixture.json

check_frontend() {
  ACF_PHASE="$1" python3 - <<'PY'
import json, os
from urllib.request import urlopen
from pathlib import Path
state = json.loads(Path('reports/acf-fixture.json').read_text())
active = os.environ['ACF_PHASE'] == 'active'
for name in ('alpha', 'beta', 'empty'):
    with urlopen('http://localhost:8080/ci-acf-' + name + '/', timeout=30) as response:
        assert response.status == 200
        html = response.read().decode('utf-8')
    assert 'CI restricted value must not render' not in html, 'Restricted field exposed'
    assert 'There has been a critical error' not in html
    if active and name in state['values']:
        assert state['values'][name] in html, (name, 'ACF binding missing')
        other = 'beta' if name == 'alpha' else 'alpha'
        assert state['values'][other] not in html, 'Values leaked between pages'
    elif not active:
        assert 'CI fallback summary' in html, 'Missing no-ACF fallback'
        assert all(value not in html for value in state['values'].values())
print('PASS: ACF frontend values, page isolation and restricted-field handling (' + os.environ['ACF_PHASE'] + ')')
PY
}
check_frontend active
wp eval-file /workspace/acf_smoke.php revise > reports/acf-fixture.json
wp eval-file /workspace/acf_smoke.php verify > reports/acf-fixture.json
check_frontend active

# Changing presentation must not erase the stored field schema or values.
# The current Docker image can retain themes that require a newer WordPress
# than the minimum-version profile. Choose only a compatible installed theme.
alternative="$(wp eval '
$themes = wp_get_themes();
ksort( $themes );
foreach ( $themes as $slug => $theme ) {
    if ( $slug !== get_stylesheet() && ! $theme->errors()
        && is_wp_version_compatible( $theme->get( "RequiresWP" ) )
        && is_php_version_compatible( $theme->get( "RequiresPHP" ) ) ) {
        WP_CLI::line( $slug );
        return;
    }
}
WP_CLI::error( "No compatible alternate theme is installed." );
')"
[ -n "$alternative" ]
wp theme activate "$alternative"
wp eval-file /workspace/acf_smoke.php verify > reports/acf-fixture.json
wp theme activate webactueel-starter
check_frontend active
wp plugin deactivate advanced-custom-fields
check_frontend inactive
wp plugin activate advanced-custom-fields
wp eval-file /workspace/acf_smoke.php verify > reports/acf-fixture.json
check_frontend active
wp eval-file /workspace/acf_smoke.php cleanup
wp plugin deactivate advanced-custom-fields
wp plugin delete advanced-custom-fields

ACF_SWITCH_THEME="$alternative" python3 - <<'PY'
import hashlib, json, os
from pathlib import Path
fixture = json.loads(Path('reports/acf-fixture.json').read_text())
report = {
    'scope': 'disposable-ci-acf-free', 'status': 'PASS',
    'commit_sha': os.environ.get('GITHUB_SHA', ''),
    'theme_sha256': hashlib.sha256(Path('dist/Webactueel-Block-Starter-1.0.5-STAGING.zip').read_bytes()).hexdigest(),
    'versions': {k: v for k, v in fixture.items() if k.endswith('_version')},
    'alternate_theme': os.environ['ACF_SWITCH_THEME'],
    'checks': ['field_group_persistence', 'page_location_rules', 'per_page_values',
               'server_side_block_bindings', 'restricted_field_not_exposed',
               'empty_value_no_fatal', 'value_update_readback',
               'theme_switch_data_preservation', 'acf_disabled_fallback',
               'reactivation_restores_values', 'fixture_cleanup'],
    'authoring_method': 'WordPress and ACF PHP APIs through WP-CLI',
    'frontend_method': 'HTTP responses from the installed theme',
    'acf_admin_ui': 'NOT_RUN', 'acf_pro_blocks_and_datastore': 'NOT_RUN',
    'full_security_certification': False,
}
Path('reports/acf-audit.json').write_text(json.dumps(report, indent=2) + '\n')
Path('reports/acf-fixture.json').unlink()
print('PASS: ACF Free compatibility receipt; PRO and editor UI remain unverified')
PY
