#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
compose=(docker compose -f tests/runtime/compose.yaml)
# Use the same WP-CLI entrypoint for every test command.
wp() { "${compose[@]}" run --rm -T cli wp "$@"; }

: "${WP_TARGET:=latest}"
: "${ENABLE_WOO:=0}"
: "${RUN_BROWSER:=1}"

# Install the archive from the package job in every matrix profile.
(cd dist && sha256sum --check SHA256SUMS.txt)
printf 'RUNTIME_THEME_SHA256=%s\n' "$(sha256sum dist/Webactueel-Block-Starter-1.0.5-STAGING.zip | cut -d' ' -f1)"
"${compose[@]}" up --wait -d database wordpress

# Probe the actual WordPress container instead of repeatedly starting WP-CLI.
ready=0
for attempt in $(seq 1 40); do
  if "${compose[@]}" exec -T wordpress test -f /var/www/html/wp-load.php && \
     "${compose[@]}" exec -T wordpress test -f /var/www/html/wp-config.php; then
    ready=1
    break
  fi
  sleep 2
done
if [ "$ready" != 1 ]; then
  "${compose[@]}" logs wordpress database
  echo 'WordPress files did not initialize' >&2
  exit 1
fi
# Report WP-CLI startup errors before seeding the database.
wp core version

if [ "$WP_TARGET" != latest ]; then
  wp core download --version="$WP_TARGET" --force
fi
wp core install --url=http://localhost:8080 --title='Webactueel CI' \
    --admin_user=ci_admin --admin_password='ci-local-only-password' \
    --admin_email=ci@example.test --skip-email
wp theme install /workspace/dist/Webactueel-Block-Starter-1.0.5-STAGING.zip --activate
wp option update permalink_structure '/%postname%/'
wp rewrite flush --hard
post_id="$(wp post create --post_type=post --post_title='Example CI Post' \
    --post_content='Testing the Webactueel Starter theme.' --post_status=publish --porcelain | tr -d '\r')"
wp term create category 'CI Category' --slug=ci-category
wp post term add "$post_id" category ci-category
wp option update posts_per_page 5
wp eval 'for ($i=1; $i<=12; $i++) { wp_insert_post(array("post_title" => "CI Archive Article " . $i, "post_content" => "Synthetic article number " . $i, "post_status" => "publish", "post_type" => "post")); }'
page_id="$(wp post create --post_type=page --post_title='Starter Page' \
    --post_content='A visible example page for CI testing.' --post_status=publish --porcelain | tr -d '\r')"
# Keep empty and invalid-block cases separate from the main editor fixture.
empty_page_id="$(wp post create --post_type=page --post_name=ci-empty-page \
    --post_title='CI Empty Page' --post_content='' --post_status=publish --porcelain | tr -d '\r')"
invalid_page_id="$(wp post create --post_type=page --post_name=ci-invalid-block \
    --post_title='CI Invalid Block' \
    --post_content='<!-- wp:heading {"level":2} --><h3 class="wp-block-heading">CI recoverable block content</h3><!-- /wp:heading -->' \
    --post_status=publish --porcelain | tr -d '\r')"
wp option update blogname 'CI-UnbrokenBrand'$(printf 'B%.0s' {1..110})
# Stress-test long unbroken content, headings and a wide Core table at small widths.
wp post create --post_type=page --post_name='ci-long-content' --post_title='CI Long Content UnbrokenTitleBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB' \
    --post_content='<!-- wp:heading --><h2 class="wp-block-heading">UnbrokenHeadingCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC</h2><!-- /wp:heading --><!-- wp:paragraph --><p>UnbrokenWordAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA</p><!-- /wp:paragraph --><!-- wp:table --><figure class="wp-block-table"><table><tbody><tr><td>Long table cell one</td><td>Long table cell two</td></tr></tbody></table></figure><!-- /wp:table -->' --post_status=publish
# This editor account exists only in the disposable test database.
if [ "${PHP_VERSION:-8.3}" = 8.3 ] && [ "$ENABLE_WOO" = 0 ]; then
  wp user create ci_editor ci-editor@example.test --role=editor \
    --user_pass='ci-editor-disposable-password'
fi
blog_id="$(wp post create --post_type=page --post_title='CI Blog' \
    --post_status=publish --porcelain | tr -d '\r')"

if [ "$ENABLE_WOO" = 1 ]; then
  wp plugin install woocommerce --activate
  wp eval-file /workspace/seed_woo.php
  if [ "${PHP_VERSION:-8.3}" = 8.3 ]; then
    # Built-in cheque is offline: no external payment provider or financial charge.
    wp option update woocommerce_cheque_settings '{"enabled":"yes","title":"CI offline cheque"}' --format=json
  fi
  wp option get woocommerce_shop_page_id
  wp option get woocommerce_cart_page_id
  wp option get woocommerce_checkout_page_id
fi

# Exercise both common Reading configurations against the installed ZIP.
wp option update show_on_front posts
curl --fail --silent --show-error --location http://localhost:8080/ > /dev/null
wp option update page_on_front "$page_id"
wp option update page_for_posts "$blog_id"
wp option update show_on_front page
# Read complete responses before testing fixture content; grep -q in a pipeline
# terminates the curl writer early and can spuriously fail with exit 23.
python3 - <<'PYVERIFY'
from urllib.request import urlopen
for path, marker in (('/', 'A visible example page'), ('/ci-blog/', 'CI Archive Article')):
    with urlopen('http://localhost:8080' + path, timeout=30) as response:
        assert response.status == 200, f'{path}: unexpected HTTP {response.status}'
        text = response.read().decode('utf-8')
        assert marker in text, f'{path}: missing expected content {marker!r}'
print('PASS: static homepage and separate posts page content')
PYVERIFY
wp option update show_on_front posts
curl --fail --silent --show-error --location 'http://localhost:8080/?s=Example' > /dev/null

if [ "$RUN_BROWSER" = 1 ]; then
  BASE_URL=http://localhost:8080 ENABLE_WOO="$ENABLE_WOO" python3 tests/runtime/browser_smoke.py
  if [ "${PHP_VERSION:-8.3}" = 8.3 ] && [ "$ENABLE_WOO" = 0 ]; then
    RUN_EDITOR_E2E=1 EDITOR_TEST_PAGE_ID="$page_id" \
      EDITOR_EMPTY_PAGE_ID="$empty_page_id" EDITOR_INVALID_PAGE_ID="$invalid_page_id" \
      RUN_SITE_EDITOR_API="$([ "$WP_TARGET" = latest ] && echo 1 || echo 0)" \
      BASE_URL=http://localhost:8080 python3 tests/runtime/admin_smoke.py
  else
    BASE_URL=http://localhost:8080 python3 tests/runtime/admin_smoke.py
  fi
fi
if [ "$ENABLE_WOO" = 1 ]; then
  if [ "${PHP_VERSION:-8.3}" = 8.3 ]; then
    RUN_OFFLINE_ORDER=1 BASE_URL=http://localhost:8080 python3 tests/runtime/woo_store_api.py
    # Inspect the generated order through WooCommerce CRUD (supports HPOS).
    wp eval '$orders=wc_get_orders(array("limit"=>10,"status"=>"on-hold")); if (!count($orders)) WP_CLI::error("Offline test order absent"); $order=$orders[0]; if ($order->get_payment_method()!=="cheque") WP_CLI::error("Unexpected test gateway"); WP_CLI::success("Synthetic offline Woo order verified");'
  else
    BASE_URL=http://localhost:8080 python3 tests/runtime/woo_store_api.py
  fi
fi
if [ "$ENABLE_WOO" = 0 ] && [ "$WP_TARGET" = latest ]; then
  # Theme-switch data preservation is a separate real WP runtime check.
  # A theme is responsible for presentation, not storing post content.
  saved="$(wp post get "$page_id" --field=post_content | tr -d '\r')"
  alternative="$(wp theme list --status=inactive --field=name | awk 'NF {print; exit}')"
  test -n "$alternative" || { echo 'No fallback WordPress theme to test switch' >&2; exit 1; }
  wp theme activate "$alternative"
  [ "$(wp post get "$page_id" --field=post_content | tr -d '\r')" = "$saved" ]
  wp theme activate webactueel-starter
  [ "$(wp post get "$page_id" --field=post_content | tr -d '\r')" = "$saved" ]
  python3 - <<'PYTHEMESWITCH'
from urllib.request import urlopen
with urlopen('http://localhost:8080/starter-page/', timeout=30) as response:
    assert response.status == 200
    body = response.read().decode('utf-8')
    assert 'Persisted from WordPress block editor on CI' in body
PYTHEMESWITCH
  echo 'PASS: real WordPress theme switch and return preserve Gutenberg post data'
  bash tests/runtime/rollback.sh
fi
if [ "$WP_TARGET" = latest ] && [ "${PHP_VERSION:-8.3}" = 8.3 ]; then
  BASE_URL=http://localhost:8080 ENABLE_WOO="$ENABLE_WOO" python3 tests/runtime/axe_audit.py
fi
# Test optional ACF only after the original no-ACF regression suite has passed.
bash tests/runtime/acf_smoke.sh
mkdir -p reports
python3 - <<'PYRECEIPT'
import hashlib, json, os, pathlib
file = pathlib.Path('dist/Webactueel-Block-Starter-1.0.5-STAGING.zip')
receipt = {
    'scope': 'disposable-ci',
    'theme_sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
    'wordpress_target': os.environ.get('WP_TARGET', 'latest'),
    'php_target': os.environ.get('PHP_VERSION', '8.3'),
    'woocommerce_enabled': os.environ.get('ENABLE_WOO') == '1',
    'payments_or_wcag_certified': False,
    'acf_free_receipt': 'acf-audit.json',
    'acf_pro': 'NOT_RUN',
    'human_wcag_em': 'NOT_RUN',
    'external_payment_provider_sandbox': 'NOT_RUN',
    'hosting_restore': 'NOT_RUN',
    'human_site_editor_ui_acceptance': 'NOT_RUN',
    'gutenberg_store_edge_cases': 'PASS' if os.environ.get('PHP_VERSION', '8.3') == '8.3' and os.environ.get('ENABLE_WOO') == '0' else 'NOT_RUN',
    'site_editor_template_parts_rest_roundtrip': 'PASS' if os.environ.get('WP_TARGET', 'latest') == 'latest' and os.environ.get('PHP_VERSION', '8.3') == '8.3' and os.environ.get('ENABLE_WOO') == '0' else 'NOT_RUN',
    'actual_theme_switch_content_preservation': 'PASS' if os.environ.get('WP_TARGET', 'latest') == 'latest' and os.environ.get('ENABLE_WOO') == '0' else 'NOT_RUN',
    'manual_screenreader_and_browser_zoom': 'NOT_RUN',
}
pathlib.Path('reports/test-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('PASS: evidence receipt', receipt['theme_sha256'])
PYRECEIPT

wp theme status webactueel-starter
wp core version
