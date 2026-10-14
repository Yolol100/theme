#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
compose=(docker compose -f tests/runtime/compose.yaml)
# Invoke WP-CLI explicitly; do not depend on the image entrypoint guessing subcommands.
wp() { "${compose[@]}" run --rm -T cli wp "$@"; }

: "${WP_TARGET:=latest}"
: "${ENABLE_WOO:=0}"
: "${RUN_BROWSER:=1}"

# Use the single archive built by the workflow package job, not a new per-matrix build.
(cd dist && sha256sum --check SHA256SUMS.txt)
printf 'RUNTIME_THEME_SHA256=%s\n' "$(sha256sum dist/Webactueel-Block-Starter-1.0.3-STAGING.zip | cut -d' ' -f1)"
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
# Fail with the real WP-CLI diagnostic rather than swallowing 40 iterations of errors.
wp core version

if [ "$WP_TARGET" != latest ]; then
  wp core download --version="$WP_TARGET" --force
fi
wp core install --url=http://localhost:8080 --title='Webactueel CI' \
    --admin_user=ci_admin --admin_password='ci-local-only-password' \
    --admin_email=ci@example.test --skip-email
wp theme install /workspace/dist/Webactueel-Block-Starter-1.0.3-STAGING.zip --activate
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
wp option update blogname 'Webactueel CI'
blog_id="$(wp post create --post_type=page --post_title='CI Blog' \
    --post_status=publish --porcelain | tr -d '\r')"

if [ "$ENABLE_WOO" = 1 ]; then
  wp plugin install woocommerce --activate
  wp eval-file /workspace/seed_woo.php
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
  BASE_URL=http://localhost:8080 python3 tests/runtime/admin_smoke.py
fi
if [ "$ENABLE_WOO" = 1 ]; then
  BASE_URL=http://localhost:8080 python3 tests/runtime/woo_store_api.py
fi
if [ "$ENABLE_WOO" = 0 ] && [ "$WP_TARGET" = latest ]; then
  bash tests/runtime/rollback.sh
fi
mkdir -p reports
python3 - <<'PYRECEIPT'
import hashlib, json, os, pathlib
file = pathlib.Path('dist/Webactueel-Block-Starter-1.0.3-STAGING.zip')
receipt = {
    'scope': 'disposable-ci',
    'theme_sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
    'wordpress_target': os.environ.get('WP_TARGET', 'latest'),
    'php_target': os.environ.get('PHP_VERSION', '8.3'),
    'woocommerce_enabled': os.environ.get('ENABLE_WOO') == '1',
    'payments_or_wcag_certified': False,
}
pathlib.Path('reports/test-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('PASS: evidence receipt', receipt['theme_sha256'])
PYRECEIPT

wp theme status webactueel-starter
wp core version
