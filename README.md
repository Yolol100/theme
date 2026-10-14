# Webactueel Block Starter

Minimal native WordPress block theme for new websites, with WooCommerce as an optional separate plugin.

This repository is the dedicated source and test workspace for **Webactueel Block Starter 1.0.3**. It is **not** an in-place upgrade for existing Webactueel Universal sites.

## Scope

- Native WordPress block templates and global styles.
- No ACF, page builder, custom PHP, JavaScript, WooCommerce overrides or demo content.
- Tests belong in this repository; only the actual theme files belong in the install ZIP.

## Quality status

The source/ZIP audit is separate from genuine WordPress and WooCommerce runtime acceptance. CI results will be recorded on the GitHub Actions page. Never treat CI success as a production or WCAG 2.2 AA certification.

See the workflow files and test scripts for the exact test scope. Test payments only in an isolated sandbox, never with real customers.

## Reference source

Original provided source: `Webactueel-Block-Starter-Source-1.0.3.zip` (SHA-256 `fdee801a2ff2302e95ea863f682ce8c936b7c022d7cf104c0d3cd563e50fcf7c`).
Original install package: `Webactueel-Block-Starter-1.0.3-STAGING.zip` (SHA-256 `b924ca4c99c33c43e15dd21cb852cd476384814950bab46ce090946f11f3179a`).

Official references: [WordPress Theme Structure](https://developer.wordpress.org/themes/core-concepts/theme-structure/), [wp-env](https://developer.wordpress.org/block-editor/reference-guides/packages/packages-env/) and [WooCommerce block themes](https://developer.woocommerce.com/docs/theming/block-theme-development/theming-woo-blocks/).
