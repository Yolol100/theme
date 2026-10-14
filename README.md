# Webactueel Starter 1.0.3

A **new, intentionally minimal block theme** built after inspecting Webactueel Universal 1.0.4. This is a clean starting point for new sites, **not an in-place update** of `webactueel-universal`.

## Install

Upload `Webactueel-Block-Starter-1.0.3-STAGING.zip` under **Appearance > Themes > Add New > Upload Theme** and activate on a test site. Requires WordPress 6.6+ and PHP 8.3+ as declared in the theme header. Set menu, logo, colors and page content via the native WordPress Site Editor. For a static homepage, assign a regular WordPress page under **Settings > Reading**; the theme deliberately has no `front-page.html`, so WordPress correctly selects `page.html`. For latest posts, `index.html` is the fallback. Nothing needs ACF, a pagebuilder, or a custom plugin.

For stores, install **WooCommerce** separately. The theme has no WooCommerce code and does not override cart, checkout or product templates; WooCommerce owns those via its official templates. Checkout verification remains a real-site staging requirement.

## Minimal content, no hidden features

The responsive base uses root-aware horizontal padding in `theme.json` to keep content off viewport edges. The release is just `style.css`, `theme.json`, six templates, three template parts, and the existing GPL license. There is no `functions.php`, custom PHP metadata, CSS or JavaScript assets, block patterns, styling presets, page builder or plugin companion. The theme is intentionally neutral and basic; create customer-specific layouts and patterns **per project**.

This starter uses Core `site-title`, `site-logo`, `navigation`, `query`, `post-title`, `post-content`, `search`, `query-title` and standard editor blocks.

## Safety / migration

**Do not activate this starter as a drop-in replacement on a site currently using Webactueel Universal 1.0.4.** The former theme has 25 built-in patterns, custom post meta fields, template variants, custom styles and WooCommerce-specific integration. Removing these theme registrations may affect existing content or editor behavior. New theme slug `webactueel-starter` deliberately prevents automatic accidental upgrades.

## Tests / build

Run `python3 -m unittest discover -s tests -v` and `python3 scripts/package.py` from the source root. The source includes a reproducible ZIP builder and an independent file-/block-comment static test suite. A real WordPress install and WooCommerce checkout have **not** been claimed without runtime evidence. Review `docs/QA.md`.

## Root padding compliance

Since version 1.0.1, top/right/bottom/left padding is explicitly defined in `theme.json` when `useRootPaddingAwareAlignments` is enabled, following the WordPress v3 reference. No site features, templates or plugins were added.

## Secure packaging since version 1.0.2

Both ZIP files are packaged from strict file allowlists. Local `.env`, `.git`, debug logs, temporary or unrelated files cannot silently enter the source distribution. Any extra runtime theme file or symbolic link aborts packaging. Negative regression tests reproduce the previously observed leakage in 1.0.1 and verify the 1.0.2 correction. This is packaging/source assurance, not WordPress integration evidence.

## Release path integrity in version 1.0.3

The source packager now rejects a symbolic link in **any ancestor path below the source root**, including `theme/` itself. The previous version only checked the final theme directory and its contents, so a linked parent could escape the intended source tree. A negative regression test demonstrates that the release aborts before writing an installation ZIP. This does not add any theme runtime features.
## GitHub continuous integration

`Starter source checks` runs source regression tests, builds both deterministic ZIPs, and validates packaging. `WordPress runtime smoke` starts disposable Docker WordPress/MariaDB sites (minimum WordPress 6.6, latest WordPress, and latest WordPress with WooCommerce), installs the generated ZIP, and uses Playwright to check representative frontend routes and responsive widths. GitHub-hosted network access is required for the Docker images, WordPress, WooCommerce and Playwright.

CI checks are **not** a production approval: Gutenberg editor save/reload, payment sandbox, manual assistive-technology tests and release rollback remain separate acceptance steps. Do not add site credentials or client data to this public repository. See `tests/runtime/` and `docs/QA.md`.
