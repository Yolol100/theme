# Webactueel Block Starter: independent staging acceptance

This repository's automated source and disposable WordPress tests DO NOT certify a production website.

## Evidence gate TH-01 through TH-16

Record for each applicable TH check: tested git SHA, installation ZIP SHA256,
site URL/hosting profile, WordPress/PHP/WooCommerce versions, responsible
reviewer, timestamp, action, expected result, observed result, screenshot/log
receipt ID, risk severity and final status (PASS, PARTIAL, NOT_RUN, FAIL, BLOCKED,
N/A with a demonstrated reason). Separate source, browser, staging and human/AT
proof. Do not count a scenario as PASS merely because the corresponding CI job
succeeded; the complete 77-case audit matrix remains the test inventory.

## Mandatory hands-on checks

- Gutenberg Site Editor: admin/editor roles; create/update post, page, menu,
  global styles, header/footer, logo; save, reopen and compare real frontend;
  invalid block content, insufficient permissions and theme-switch preservation.
- WCAG 2.2 AA: WCAG-EM sampling including keyboard, focus, screenreader,
  page zoom/reflow, labels, hover states and store checkout. axe is advisory,
  never a substitute for assistive-technology review.
- WooCommerce where used: guest and authenticated order using only a sanctioned
  offline-test method/provider sandbox; variants, stock, shipping/tax rules,
  account, checkout validation and customer/session isolation. Never real money.
- SEO and performance: one metadata/robots/schema owner, Lighthouse lab plus
  actual host/RUM p75 (LCP<=2.5s, INP<=200ms, CLS<=0.1) when field data exists;
  CDN cache (cold/warm) and cart/account/checkout private-cache behavior.
- Release: clean install exact tested ZIP, restore a complete staging database
  and uploads backup after controlled damage, post-restore verification, retest
  and independent owner signoff. GitHub's disposable rollback drill is not
  evidence that the actual host's backup process works.

## Status and signoff

Current state is SOURCE + DISPOSABLE-RUNTIME SMOKE GO only. Staging/production GO
requires every applicable independent TH-01..TH-16 gate, all required scenario
receipts, zero unresolved medium/high/critical findings and owner/QA signoff.
Keep client details and real account/payment credentials out of public CI.
