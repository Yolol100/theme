# Webactueel Starter — current QA scope and evidence

**Status: source and disposable WordPress smoke testing. NOT production approved.**
This is an intentionally minimal block theme for new sites, not an update of an
older universal theme. No ACF, custom WordPress PHP/JS or WooCommerce overrides.

## Baseline verified 14 October 2026

- GitHub HEAD `e00d6008b28aa0c6fb9bed0b5aca51422a9557f8`:
  [source checks 24/24](https://github.com/Yolol100/theme/actions/runs/38622464211)
  and [3/3 runtime combinations](https://github.com/Yolol100/theme/actions/runs/38622464208) passed.
- Theme ZIP: 12 files, SHA-256
  `b924ca4c99c33c43e15dd21cb852cd476384814950bab46ce090946f11f3179a`.
- These were basic route/viewport and install smoke assertions. They did NOT
  test Gutenberg editing/save/reopen, real payment checkout or full WCAG.

The newer workflow in this repository increases coverage with one package
artifact per runtime run, PHP 8.4, real content assertions, admin login,
WooCommerce Store API carts and synthetic offline checkout, an axe-core advisory scan and an isolated database/uploads restore
exercise. Read the **actual GitHub Actions result on the latest commit** before
claiming those new tests have passed. A newly committed test is not proof until
its job has completed successfully.

## Theme acceptance

Use the authoritative TH-01 through TH-16 matrix and the 77 scenario inventory
in `docs/77-scenarios.json`. Source/static, controlled-runtime, authenticated
browser, independent staging, assistive-technology and external sandbox
assertions are **different evidence classes**. A CI success must never
promote the entire 77-scenario inventory to PASS.

Still needs appropriate real-world independent checks:

1. Gutenberg admin/editor save, reopen and frontend comparison for posts,
   menus, header/footer, site-logo and global styles.
2. WCAG 2.2 AA sampling by a human with keyboard, mobile, VoiceOver/NVDA,
   focus, zoom and reflow; automated axe signals are not certification.
3. WooCommerce cart/checkout, variations, order status, payment provider
   sandbox, account and cached session isolation as used on the target site.
4. Host-specific Core Web Vitals, performance, caching, SEO metadata owner,
   real plugins and target devices/browsers.
5. Actual staging host database/uploads restore and independent owner approval.

See `docs/STAGING-ACCEPTANCE.md` for receipts, review and final approval.
Never put real credentials, customer data or order information in public Actions
artifacts. A missing scenario receipt stays NOT_RUN (or PARTIAL), not PASS.
