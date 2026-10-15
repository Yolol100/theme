# QA and evidence scope

**Source and disposable runtime checks only; NOT production approved.** The source ZIP contains the 77 original scenarios in `77-scenarios.json`; it is an inventory, not 77 recorded successes. Apply `PASS`, `FAIL`, `PARTIAL`, `NOT_RUN`, `BLOCKED` or justified `N/A` with matching commit, ZIP hash and actual evidence.

## Automated CI

- Source tests: syntax, allowed files, packaging/rebuild, exact ZIP/hash, ACF and acceptance contract guards.
- Disposable WordPress/PHP matrix: installation, routes, Gutenberg/API/CLI save-readback, long-content 320–1920px, keyboard and axe advisory checks, WooCommerce synthetic carts/offline orders where active, optional ACF Free fields and isolated database/uploads recovery.
- A test skipped by a flag/missing dependency is **`NOT_RUN`**, never `PASS`. Browser checks also detect PHP frontend warnings and missing first-party assets. A green workflow proves only checks actually executed; read the current job logs and receipts.

## Independent evidence required

1. Human Gutenberg Site Editor/admin/editor permission tasks and frontend comparison.
2. WCAG 2.2 AA sampling using **W3C WCAG-EM 2.0**, real keyboard/zoom and assistive-technology review; axe is supplemental.
3. Target WooCommerce extensions, *actual* provider sandbox (not cheque/offline), account and cache/session isolation.
4. Real host/CDN/Core Web Vitals, SEO metadata ownership, backups and **host-side restore**.
5. Owner/independent QA signoff with private, verifiable receipts.

Use [STAGING-ACCEPTANCE.md](STAGING-ACCEPTANCE.md) and `staging-acceptance.example.json`. Never upload client credentials, payment tokens or production logs to public GitHub. **NO production GO** without mandatory real-environment and human gates.
