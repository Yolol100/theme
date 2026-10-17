# Webactueel Block Starter 1.0.5

Minimal native **WordPress block theme** for *new* sites; **not** a drop-in upgrade for Webactueel Universal. The installable theme has 12 files: six templates, three template parts, `theme.json`, stylesheet metadata and GPL license. No PHP/JS, ACF dependency, page builder or custom WooCommerce checkout code.

## Why this project exists

A new WordPress site should be able to start with native blocks and a small, reviewable theme rather than inherit a large page-builder or plugin stack. This starter keeps layout structure inside Gutenberg while making compatibility, packaging and staging decisions explicit.

## What this starter demonstrates

**For website owners:** a lean WordPress foundation with editable native blocks instead of a compulsory page builder.

**For reviewers:** theme templates, reusable layout parts and design tokens that can be inspected independently from the test and package pipeline.

**Try it safely:** run the [build and verification commands](#verify-and-package), install the generated theme ZIP on a **new staging WordPress site**, and inspect the editor, responsive templates and navigation before creating any client-specific variation. This repository is a starter, **not** a copy of an existing Webactueel client design.

**Looking for actual design work?** See [Spring Architecten](https://andrewbaeten.nl/spring-architecten/), [RBMB](https://andrewbaeten.nl/rbmb/) and [more independent website case studies](https://andrewbaeten.nl/category/cases/). Those projects demonstrate design delivery; they are **not** presented as sites built with this exact starter.

## What to review

| Engineering decision | Inspect |
| --- | --- |
| Native block templates and design tokens | [Theme architecture](docs/ARCHITECTURE.md) and the installable theme source |
| Repeatable packaging and validation | [Source workflow](.github/workflows/ci.yml), [runtime matrix](.github/workflows/wordpress-runtime.yml) and [tests](tests/) |
| Release limits and human checks | [QA contract](docs/QA.md) and [staging acceptance](docs/STAGING-ACCEPTANCE.md) |

**Evidence boundary:** This is a reproducible starter and testing example—not a public client website, a visual design case study or a production-ready upgrade for an existing theme.

## Compatibility and setup

- WordPress 6.6+ and PHP 8.3+ per theme header; verify the chosen target versions.
- Core/Gutenberg owns pages and layout. ACF is optional structured data; field groups must be created deliberately. WooCommerce owns products, cart and checkout.
- [Architecture](docs/ARCHITECTURE.md) · [QA](docs/QA.md) · [staging/GO decision](docs/STAGING-ACCEPTANCE.md) · [77 scenarios](docs/77-scenarios.json).

## Verify and package

```bash
python3 -m unittest discover -s tests -v
python3 scripts/package.py
(cd dist && sha256sum --check SHA256SUMS.txt)
```

CI runs source checks and four isolated runtime profiles (WordPress 6.6/current; PHP 8.3/8.4; optional WooCommerce and ACF Free). It downloads **one exact hashed ZIP** into runtime jobs. Source checks, browser/editor tests, API/CLI tests and human tests are **different evidence classes**. Review the *latest* [Actions](https://github.com/Yolol100/theme/actions) and failures before using any result.

Installable ZIP: `Webactueel-Block-Starter-1.0.5-STAGING.zip` (only `webactueel-starter/`). Source ZIP additionally includes tests/docs. Neither CI nor the starter certifies a live shop, all plugins, WCAG 2.2 AA, real payment or hosting rollback. Production requires separate [staging acceptance](docs/STAGING-ACCEPTANCE.md). Never commit real credentials or customer data.

For a client site, create a **separate fork/copy** with its own slug, text domain, design, templates, plugin inventory and tests. Keep this starter lean and independently reproducible.

Sources: [WordPress themes](https://developer.wordpress.org/themes/core-concepts/theme-structure/) · [WooCommerce blocks](https://developer.woocommerce.com/docs/theming/block-theme-development/cart-and-checkout) · [WCAG-EM](https://www.w3.org/WAI/test-evaluate/conformance/wcag-em/).
