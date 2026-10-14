# Webactueel Block Starter 1.0.4

Minimal, independent native WordPress block theme for new projects. The theme
contains 12 installable files, 6 block templates, 3 reusable template parts,
`theme.json`, a GPL license and the stylesheet metadata. WooCommerce is optional
and retains responsibility for shopping features. No ACF, custom PHP, JavaScript,
checkout overrides, sample layouts or private information ship in the theme.

**Not a drop-in upgrade for Webactueel Universal 1.0.4.** Different slug and
project scope: no automatic migration of an existing site.

## Build and test

```bash
python3 -m unittest discover -s tests -v
python3 scripts/package.py
(cd dist && sha256sum --check SHA256SUMS.txt)
```

GitHub Actions automatically tests the above on push/PR. The runtime workflow
builds a single exact theme ZIP, downloads that same archive into isolated
WordPress/MariaDB configurations, installs it, and runs content/browser, admin,
Store API (when WooCommerce is active) and restore smoke tests. Tested results
and their recorded ZIP hashes are retained as temporary Actions artifacts.

Run the Docker runtime smoke locally with Docker Compose and Playwright installed:

```bash
python3 scripts/package.py
WP_TARGET=latest PHP_VERSION=8.3 ENABLE_WOO=0 bash tests/runtime/run.sh
# Remove disposable state (never run against a real database):
docker compose -f tests/runtime/compose.yaml down -v --remove-orphans
```

The test matrix includes the minimum declared WordPress 6.6/PHP 8.3 profile,
current WordPress/PHP 8.3 and WooCommerce on current WordPress/PHP 8.3 and 8.4.
WordPress's own editor, menus and WooCommerce extend the theme; the CI tools
never add backend or payment code to the theme ZIP.

## Release evidence and limits

- Baseline source ZIP and exact installation ZIP SHA-256: `0c64eaf614726ebfccf771b91740a8ea1f0318b6fc2299a329029e8dbf989b38`.
- Every build must verify its own `dist/SHA256SUMS.txt` and link to its commit/run.
- Installable filename: `Webactueel-Block-Starter-1.0.4-STAGING.zip`.
- See `docs/QA.md`, `docs/77-scenarios.json`, and `docs/STAGING-ACCEPTANCE.md`.
- A green GitHub Actions run validates only the assertions actually executed.
  It is **not** a WCAG 2.2 AA certificate, real-money checkout test, hosting
  performance score, or permission to deploy to a client site.
- CI uses synthetic local-only credentials; never commit actual logins, client
  data or payment-provider tokens to this public repository.

## References

[WordPress Theme Structure](https://developer.wordpress.org/themes/core-concepts/theme-structure/)
| [WordPress Theme Testing](https://developer.wordpress.org/themes/advanced-topics/testing/)
| [WooCommerce Store API](https://developer.woocommerce.com/docs/apis/store-api/)
| [W3C WCAG-EM](https://www.w3.org/WAI/test-evaluate/conformance/wcag-em/)
