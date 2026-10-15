# Webactueel Block Starter 1.0.5

Minimal native **WordPress block theme** for *new* sites; **not** a drop-in upgrade for Webactueel Universal. The installable theme has 12 files: six templates, three template parts, `theme.json`, stylesheet metadata and GPL license. No PHP/JS, ACF dependency, page builder or custom WooCommerce checkout code.

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
