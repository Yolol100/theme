#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
compose=(docker compose -f tests/runtime/compose.yaml)
wp() { docker compose -f tests/runtime/compose.yaml run --rm -T cli wp "$@"; }
mkdir -p reports
printf '{"status":"FAIL","scope":"disposable-wordpress","production_approved":false}\n' > reports/external-runtime.json
trap 'docker compose -f tests/runtime/compose.yaml down -v --remove-orphans >/dev/null 2>&1 || true' EXIT
python3 scripts/validate_external_theme_zip.py --zip "dist/$QA_ZIP_FILENAME" --sha256 "$QA_ZIP_SHA256" --slug "$QA_THEME_SLUG" --report reports/external-zip.json
docker compose -f tests/runtime/compose.yaml up --wait -d database wordpress
for attempt in $(seq 1 40); do
  docker compose -f tests/runtime/compose.yaml exec -T wordpress test -f /var/www/html/wp-config.php && break
  sleep 2
done
docker compose -f tests/runtime/compose.yaml exec -T wordpress test -f /var/www/html/wp-config.php
wp core version
if [ "$WP_TARGET" != latest ]; then wp core download --version="$WP_TARGET" --force; fi
wp core install --url=http://localhost:8080 --title='Private Theme QA' --admin_user=ci_admin --admin_password=ci-disposable-only --admin_email=ci@example.test --skip-email
wp theme install "/workspace/dist/$QA_ZIP_FILENAME" --activate
wp theme is-active "$QA_THEME_SLUG"
wp option update permalink_structure '/%postname%/'
wp rewrite flush --hard
page_id="$(wp post create --post_type=page --post_title='QA Roundtrip' --post_content='Initial test' --post_status=publish --porcelain | tr -d '\r')"
wp post update "$page_id" --post_content='Persisted test'
wp post get "$page_id" --field=post_content | grep -F 'Persisted test' >/dev/null
if [ "$ENABLE_WOO" = 1 ]; then wp plugin install woocommerce --activate; wp plugin is-active woocommerce; fi
if [ "$ENABLE_ACF" = 1 ]; then wp plugin install advanced-custom-fields --activate; wp plugin is-active advanced-custom-fields; fi
curl -fsS http://localhost:8080/ >/dev/null
python3 tests/runtime/external_zip_browser.py
php_errors="$(docker compose -f tests/runtime/compose.yaml exec -T wordpress sh -c "if test -f /var/www/html/wp-content/debug.log; then grep -Eic 'PHP (Warning|Notice|Deprecated|Fatal|Parse)|Uncaught (Exception|Error)' /var/www/html/wp-content/debug.log || true; else echo 0; fi" | tr -d '\r')"
[ "$php_errors" = 0 ] || { echo 'PHP diagnostic detected' >&2; exit 1; }
QA_ACTUAL_WP="$(wp core version | tail -n1 | tr -d '\r')" QA_ACTUAL_PHP="$(wp eval 'echo PHP_VERSION;' | tail -n1 | tr -d '\r')" python3 - <<'PY'
import json, os
from pathlib import Path
data={'status':'PASS','scope':'disposable-wordpress','caller_commit':os.environ['QA_SOURCE_SHA'],'harness_commit':os.environ['QA_HARNESS_SHA'],'zip_sha256':os.environ['QA_ZIP_SHA256'],'theme_slug':os.environ['QA_THEME_SLUG'],'wordpress_version':os.environ['QA_ACTUAL_WP'],'php_version':os.environ['QA_ACTUAL_PHP'],'install_activation':'PASS','gutenberg_cli_readback':'PASS','woocommerce':'PASS' if os.environ['ENABLE_WOO']=='1' else 'NOT_RUN','acf_free':'PASS' if os.environ['ENABLE_ACF']=='1' else 'NOT_RUN','gutenberg_editor_ui':'NOT_RUN','lighthouse_multi_run':'NOT_RUN','wcag_em_manual':'NOT_RUN','production_approved':False}
Path('reports/external-runtime.json').write_text(json.dumps(data,indent=2)+'\n')
PY
