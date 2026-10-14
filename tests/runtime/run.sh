#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
compose=(docker compose -f tests/runtime/compose.yaml)
wp() { "${compose[@]}" run --rm -T cli "$@"; }

: "${WP_TARGET:=latest}"
: "${ENABLE_WOO:=0}"
: "${RUN_BROWSER:=1}"

python3 scripts/package.py
"${compose[@]}" up --wait -d database wordpress

# The WordPress image populates the shared WordPress volume on first start.
ready=0
for attempt in $(seq 1 40); do
  if wp core version >/dev/null 2>&1; then ready=1; break; fi
  sleep 3
done
if [ "$ready" != 1 ]; then
  "${compose[@]}" logs wordpress database
  echo 'WordPress files did not initialize' >&2
  exit 1
fi

if [ "$WP_TARGET" != latest ]; then
  wp core download --version="$WP_TARGET" --force
fi
wp core install --url=http://localhost:8080 --title='Webactueel CI' \
    --admin_user=ci_admin --admin_password='ci-local-only-password' \
    --admin_email=ci@example.test --skip-email
wp theme install /workspace/dist/Webactueel-Block-Starter-1.0.3-STAGING.zip --activate
wp option update permalink_structure '/%postname%/'
wp rewrite flush --hard
wp post create --post_type=post --post_title='Example CI Post' \
    --post_content='Testing the Webactueel Starter theme.' --post_status=publish
page_id="$(wp post create --post_type=page --post_title='Starter Page' \
    --post_content='A visible example page for CI testing.' --post_status=publish --porcelain | tr -d '\r')"
wp option update blogname 'Webactueel CI'

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
wp option update show_on_front page
wp option update page_on_front "$page_id"
curl --fail --silent --show-error --location http://localhost:8080/ > /dev/null
wp option update show_on_front posts
curl --fail --silent --show-error --location 'http://localhost:8080/?s=Example' > /dev/null

if [ "$RUN_BROWSER" = 1 ]; then
  BASE_URL=http://127.0.0.1:8080 ENABLE_WOO="$ENABLE_WOO" python3 tests/runtime/browser_smoke.py
fi
wp theme status webactueel-starter
wp core version
