# Architecture: small, native and portable

`theme/webactueel-starter/` is the **only** installable directory. Standard required files: `style.css`, `templates/index.html`. This starter also has `theme.json`, `templates/{page,single,archive,search,404}.html`, `parts/{header,footer,post-list}.html` and `LICENSE.txt`. `style.css` supplies metadata; its frontend styles are **not automatically loaded** for this block theme. Verify effective `theme.json` CSS in the browser.

All other directories are tooling: `scripts/` builds ZIPs/validates receipts, `tests/` contains disposable regressions, `docs/` holds QA and `.github/workflows/` runs CI. Add optional `patterns/`, `styles/`, `assets/`, `functions.php`, `woocommerce/` or `acf-json/` **only when required**. The packager intentionally allow-lists deployable files; update the allow-list and tests when you extend a fork.

## Content and plugins

- Prefer **Core block → style/variation → pattern/part → supported binding → structured fields → custom block**, in that order. Keep shared header/footer editable in Site Editor. WordPress template hierarchy falls back to `index.html`; check a static homepage and posts page when configured.
- Theme = presentation. Companion plugin/MU-plugin = persistent CPTs, taxonomies, field models, server rules and integration logic. WooCommerce = catalog, stock, cart, checkout, orders and taxes. Avoid fragile CSS selectors that depend on WooCommerce block internals.
- **ACF is optional**, and does not invent per-page fields. Create field groups/location rules; WordPress stores values per post ID. Core `core/post-meta` bindings need registered metadata with `show_in_rest=true` and supported attributes. The newer **ACF visual editor/datastore bindings** require ACF **PRO 6.8.1+, WordPress 6.7+ and datastore enabled** (official requirements checked 2026-10-15). The CI's ACF Free server-rendering tests do not prove that PRO UI.
- No bundled payments, custom checkout, ACF PRO features, customer-specific design or universal integration guarantee. Build customer-specific layouts in separate project repositories, not this baseline.

Code comments should explain *why*, in plain English; retain machine-readable WordPress block delimiters and human attribution/license data. Run editor and frontend regression tests after every change; never classify a skipped test as passed.

Sources: [Theme structure](https://developer.wordpress.org/themes/core-concepts/theme-structure/) · [Block bindings](https://developer.wordpress.org/block-editor/reference-guides/block-api/block-bindings/) · [ACF requirements](https://www.advancedcustomfields.com/resources/block-bindings/) · [Woo blocks](https://developer.woocommerce.com/docs/theming/block-theme-development/cart-and-checkout).
