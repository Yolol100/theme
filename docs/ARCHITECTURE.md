# Starter architecture and integration guide

Reviewed on 15 October 2026 against the sources below. This is a foundation for
new projects, not a finished design, a page-field generator, or a guarantee that
every plugin and hosting combination will work without project-specific tests.

## What belongs where

| Location | Purpose |
| --- | --- |
| `theme/webactueel-starter/` | The only directory installed as a WordPress theme. |
| `style.css` | Theme identity, version, license and minimum versions. It contains no frontend CSS. |
| `theme.json` | Native editor controls, colors, spacing, layout and the small reflow rule. |
| `templates/index.html` | Required block-theme fallback and default blog listing. |
| `templates/page.html`, `single.html` | Page and post content; neither owns custom data. |
| `templates/archive.html`, `search.html`, `404.html` | Archive, search and missing-page views. |
| `parts/header.html`, `footer.html` | Shared site regions, editable in the Site Editor. |
| `parts/post-list.html` | Shared inherited Query block for listings. |
| `LICENSE.txt` | The distribution license. |
| `scripts/` | Archive building and acceptance-record validation. Not installed. |
| `tests/`, `tests/runtime/` | Source checks and disposable WordPress tests. Not installed. |
| `docs/`, `.github/workflows/` | Documentation and CI configuration. Not installed. |
| `dist/`, `reports/` | Ignored build output and temporary test evidence. |

These names follow WordPress conventions. Renaming `style.css`, `theme.json`,
`templates/` or referenced template parts would break discovery or references.
There is no need for an empty `functions.php`, `assets/`, `inc/`, `patterns/`,
`styles/`, `woocommerce/` or `acf-json/` directory. Add one only when a particular
project uses it. Empty optional-scaffolding directories are no longer generated
in the source archive.

The installation remains 12 files. The source archive is larger because it also
contains the tests and documentation. The release file list is intentionally
strict: when building a customized fork, update it and its tests to include the
new, required files. Do not bypass it with a recursive wildcard.

## Suitable projects and limits

Use this as a starting point for business sites, portfolios, content sites and
WooCommerce stores. Configure a static front page and a separate posts page
through WordPress Reading settings. Add project-specific layouts through Core
blocks, patterns or templates rather than a second page builder by default.
WooCommerce supplies its own catalog, product, cart and checkout templates.
The starter does not bundle payment, shipping, tax or order code.

Each project still needs its design, content model, chosen extensions, metadata
owner, caching rules and acceptance tests. Multisite, multilingual/RTL layouts,
memberships, bookings, unusual post types and every possible commerce extension
are not universally certified by this repository. Default labels are English;
translate editorial template text for the target site. This package is not a
WordPress.org directory submission; directory assets and submission review are
separate work, not prerequisites for privately installing a block theme.

## ACF fields per page

ACF is optional and is not bundled with the theme. Installing ACF does not make
the theme invent a different content model for every page. A developer or an
authorized automation must define the field groups and location rules first.

1. Create the required fields in ACF and apply the group to pages, a specific
   page, or a selected page template. WordPress stores each page's values under
   that page's ID; a shared field group does not mean shared values.
2. Save a value on the intended page. A field input and a visible frontend value
   are different things: connect the field to a block or a rendering component.
3. For simple text, use a supported Core block with an `acf/field` binding. Allow
   access to that field in the editor UI only when editors may publish its value.
   ACF's newer visual binding/datastore features have separate PRO and WordPress
   version requirements; server-side bindings are tested independently here.
4. For complex repeaters, Flexible Content or bespoke ACF Blocks, use a
   project-specific plugin/component and the appropriate ACF PRO license. HTML
   block templates do not execute embedded PHP such as `get_field()`.
5. Keep persistent field schemas, post types and business rules in a companion
   plugin when they must survive a theme switch. Use ACF Local JSON or exported
   PHP for version control. ACF defaults to the active theme's `acf-json/` path;
   explicitly configure load/save paths when the companion plugin owns it.
   Apply save-path filters only to the groups that plugin owns.

Use stable English field names and keys. Renaming a field or changing its return
format requires a migration review. Escape values at their final output boundary:
plain text, URLs, attributes and permitted HTML have different requirements.
Never expose passwords, tokens or private data through block bindings.

### Tested contract

The `acf_smoke` scripts install ACF Free 6.8.10 from its official release archive
and verify the published SHA-256 before installation. They run after the original
no-ACF checks on each existing WordPress/PHP/WooCommerce profile. They create real
field groups through PHP APIs, check page-specific location rules and separate
values, read rendered Core block bindings, update values, switch themes, disable
and reactivate ACF, and remove the fixtures. Results belong in `acf-audit.json`.

A passing record covers those assertions only. It does not prove manual ACF field
creation, the PRO datastore, ACF Blocks, repeaters, every field type or every
third-party integration. ACF PRO tests require an authorized PRO installation;
no license or private plugin archive belongs in this public repository.

## Comments and maintenance

Use short English comments to explain constraints, workarounds and intent. Avoid
repeating the code or calling an unexecuted test a success. Preserve WordPress's
`<!-- wp:... -->` block delimiters, theme metadata, licenses, URLs, field keys and
other machine-readable content; they are not prose comments to rewrite.

Keep each failure visible. An HTTP/REST or editor-store test is not a human UI
or screen-reader test. See [staging acceptance](STAGING-ACCEPTANCE.md) for the
remaining human, hosting and payment-provider checks.

## Sources

- [WordPress theme structure](https://developer.wordpress.org/themes/core-concepts/theme-structure/)
- [WordPress templates](https://developer.wordpress.org/themes/templates/templates/)
- [WooCommerce block-theme integration](https://developer.woocommerce.com/docs/theming/block-theme-development/theming-woo-blocks/)
- [ACF installation](https://www.advancedcustomfields.com/resources/installation/)
- [ACF 6.8.10 release and archive digest](https://github.com/AdvancedCustomFields/acf/releases/tag/6.8.10)
- [ACF bindings implementation for the tested version](https://github.com/AdvancedCustomFields/acf/blob/6.8.10/src/Blocks/Bindings.php)
- [ACF binding UI and requirements](https://www.advancedcustomfields.com/resources/block-bindings/)
- [ACF Local JSON](https://www.advancedcustomfields.com/resources/local-json/)
- [ACF field-access security](https://www.advancedcustomfields.com/resources/acf-security-principles/)

The Webactueel WordPress knowledge bank and historical Library audits informed
the scope. They do not replace current source or runtime evidence. The Library
YouTube channel catalog was checked; no verified video transcript or comment set
was used as proof of this theme's compatibility.
