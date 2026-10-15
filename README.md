# Webactueel Block Starter 1.0.5

Minimal, independent native WordPress block theme for new projects. The theme
contains 12 installable files, 6 block templates, 3 reusable template parts,
`theme.json`, a GPL license and the stylesheet metadata. WooCommerce is optional
and retains responsibility for shopping features. No ACF, custom PHP, JavaScript,
checkout overrides, sample layouts or private information ship in the theme.

**Not a drop-in upgrade for Webactueel Universal 1.0.4.** Different slug and
project scope: no automatic migration of an existing site.

## Why this project matters

A new client site should not need an oversized starter theme or hidden dependencies. This project keeps the installable block theme small and delegates content editing to WordPress Core and shop behavior to WooCommerce.

**What I built:** a reproducibly packaged block-theme starter with native templates and parts, a `theme.json` configuration and automated installation/smoke-test workflows. The public repository contains its source, tests and staging-acceptance criteria.

**Engineering decisions:** keep site-specific functionality outside the theme; test the exact packaged ZIP across isolated WordPress/PHP configurations; require separate human staging acceptance before a client release.

**Technical reviewers:** see [QA and test scope](docs/QA.md), [staging acceptance](docs/STAGING-ACCEPTANCE.md) and [the GitHub Actions workflows](.github/workflows/). These are inspectable engineering checks, not proof of real-client deployment or full accessibility conformance.

**Developer:** [Andrew Baeten — WordPress Developer & Web Designer](https://github.com/Yolol100) · [Website portfolio](https://andrewbaeten.nl/category/cases)

## Architecture and optional custom fields

See [the architecture and integration guide](docs/ARCHITECTURE.md) for file
ownership, naming, ACF per-page fields and the limits of a general starter.
ACF is optional; field schemas and frontend bindings must be configured for each
project. The CI tests ACF Free separately and does not certify ACF PRO features.

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

- Previous 1.0.4 installation ZIP (rollback) SHA-256: `ac880c7b65c95b30d0b24429172476bc32f1173c86ab46a3154fa1bb5e0a9550`.
- Every build must verify its own `dist/SHA256SUMS.txt` and link to its commit/run.
- Installable filename: `Webactueel-Block-Starter-1.0.5-STAGING.zip`.
- See `docs/QA.md`, `docs/77-scenarios.json`, and `docs/STAGING-ACCEPTANCE.md`.
- Human WCAG-EM 2.0, a real payment-provider sandbox and hosting rollback
  require a *separate actual staging environment and reviewer*. Use the
  fail-closed example receipt `docs/staging-acceptance.example.json` and
  validator `scripts/validate_staging_acceptance.py`; CI cannot certify them.
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
