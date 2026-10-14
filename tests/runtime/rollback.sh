#!/usr/bin/env bash
# Isolated, deterministic database+uploads rollback drill. Never run on production.
set -euo pipefail
cd "$(dirname "$0")/../.."
compose=(docker compose -f tests/runtime/compose.yaml)
wp() { "${compose[@]}" run --rm -T cli wp "$@"; }
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

before="$(wp option get blogdescription | tail -n 1 | tr -d '\r')"
"${compose[@]}" exec -T database mariadb-dump -uwordpress -pwordpress-ci wordpress > "$tmp/wordpress.sql"
test -s "$tmp/wordpress.sql"
"${compose[@]}" exec -T wordpress sh -c \
  'mkdir -p /var/www/html/wp-content/uploads/ci-rollback && printf "restore-ok" > /var/www/html/wp-content/uploads/ci-rollback/marker.txt'
"${compose[@]}" exec -T wordpress tar -C /var/www/html/wp-content -cf - uploads > "$tmp/uploads.tar"
test -s "$tmp/uploads.tar"

wp option update blogdescription 'CI changed after backup'
"${compose[@]}" exec -T wordpress rm -f /var/www/html/wp-content/uploads/ci-rollback/marker.txt
[[ "$(wp option get blogdescription | tail -n 1 | tr -d '\r')" == 'CI changed after backup' ]]
"${compose[@]}" exec -T database mariadb -uwordpress -pwordpress-ci wordpress < "$tmp/wordpress.sql"
"${compose[@]}" exec -T wordpress tar -C /var/www/html/wp-content -xf - < "$tmp/uploads.tar"
after="$(wp option get blogdescription | tail -n 1 | tr -d '\r')"
[[ "$before" == "$after" ]]
"${compose[@]}" exec -T wordpress test -f /var/www/html/wp-content/uploads/ci-rollback/marker.txt
wp theme status webactueel-starter > /dev/null
printf 'PASS: isolated database and uploads backup/restore (not a hosting rollback)\n'
