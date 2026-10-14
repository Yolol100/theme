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

The disposable `tests/runtime/axe_audit.py` generates **advisory** axe-core findings for representative synthetic WordPress pages; it is not a WCAG-EM sample or human AT review.

CI also exercises the built-in **cheque/offline** method with fully synthetic data, solely in an isolated database. This is not a payment-provider sandbox test or proof that real payment, tax and shipping extensions work.

## Expanded acceptance track (15 October 2026)

This is a **manual test runbook**, not a report of tests already performed. The
CI workflows use local synthetic accounts on disposable containers. For every
item below, record the **full git SHA, exact installation ZIP SHA-256, test date,
reviewer, site/host, expected and actual result, and evidence ID**. Keep private
screenshots, personal data, credentials, transactions and host-backup locations
outside this public repository and GitHub Actions artifacts.

### 1. Gutenberg + responsive (TH-05, TH-08)

Use the *exact tested ZIP* on an isolated staging installation and verify both
administrator and editor users (separate accounts). Open the Gutenberg user
interface; create and publish a post and page with paragraph, long H1/H2,
buttons, nested columns, lists, table, image with alt text, and empty content.
Save, close, reopen and compare rendered content and computed styles to the
editor. Test real UI interactions, not merely REST API or block data-store calls.
As administrator, edit and restore **header, footer, navigation and Global
Styles** in Site Editor. Prove the editor cannot access privileged settings.
Exercise invalid-block recovery and a controlled theme switch with content
preservation. Compare 320, 375, 390, 768, 1024, 1440 and 1920 CSS-pixel widths
in Chromium, Firefox and Safari where available; test landscape and portrait.
Test **actual browser zoom at 200%** and reflow at 320 CSS px (equivalent to
1280 CSS px at 400% zoom). Document exceptions for genuinely two-dimensional
content such as tables; the *document* must not overflow unnecessarily.

### 2. Independent human WCAG-EM 2.0 evaluation (TH-09)

Use the [W3C WCAG-EM 2.0 method](https://www.w3.org/TR/wcag-em-2/) with WCAG
2.2 AA as the target: (1) scope, (2) explore functionality, (3) select a
representative sample, (4) evaluate, and (5) report. Include at least homepage,
post/page with long content, search result and empty state, 404, menu open/closed,
Gutenberg editing and the complete WooCommerce checkout including errors.
Evaluate keyboard-only Tab/Shift+Tab/Enter/Space/Escape, visible and unobscured
focus, skip/landmark/heading order, 200% zoom/reflow, alt text, label/error/status
announcements, contrast, accessible names, pointer targets and reduced motion.
Run human assistive-technology sessions (e.g. NVDA/Firefox and VoiceOver/Safari)
with actual task outcomes; record tester, version and proof. Axe-core output is
**supplemental** and cannot mark this human gate PASS by itself. Issues in
WooCommerce/plugins must retain their owner and remain open until independently
resolved.

### 3. Payment provider sandbox (TH-13)

Only on **authorized staging**, with all live keys disabled, an explicit
provider-specific *test mode* shown and **no real funds**. Select the actual
provider installed for the target (Stripe, WooPayments, Mollie, etc.); do not
presume a provider. Use its official test payment method and test values for
successful, declined and (where applicable) authentication-required payments.
Verify guest/registered checkout, order and stock state, webhook retry, failure
message, customer/session isolation and sandbox refund if supported. Avoid
production mail, shipment, analytics and integrations. Capture *redacted* order
reference and test-mode confirmation. The existing synthetic **cheque** test
has no provider transaction and must **not** count as a sandbox PASS.
[WooCommerce testing orders](https://woocommerce.com/document/managing-orders/testing-orders/).

### 4. Hosting backup and rollback (TH-16)

On authorized, disposable staging **only**, first confirm host, environment,
point-in-time backup retention, restore permissions, maintenance window and
independent owner approval for the controlled restore exercise. Record the
backup ID and WP/PHP/database versions privately. Verify a recoverable database
and complete uploads/files backup; perform a controlled change and **restore
using the actual host's recovery tool**, not the CI Docker database. Confirm
front page, admin login, permalink routing, uploads, edited content, theme
activation, critical flows, cart isolation and correct cache/HTTPS behavior
*after* restore. Log restore time, failures and fallback. Do **not** add a
workflow that automatically deletes a live database, switches a production
site, or invokes hosting restore without explicit environment authorization.

### 5. Acceptance receipt / fail-closed gate

Start from `docs/staging-acceptance.example.json` in a **private workspace**.
Fill all six gates with actual reviewer and dated evidence. Set `PASS` only
when the corresponding task has been observed, not when a test was merely
planned. The fields are documented by `scripts/validate_staging_acceptance.py`.
Run:

```bash
python3 scripts/validate_staging_acceptance.py private-receipt.json \
  --zip dist/Webactueel-Block-Starter-1.0.5-STAGING.zip \
  --expected-commit <full-intended-commit-sha> --require-complete
```

The packaged example intentionally returns `NO_GO`. Even when a complete
receipt validates, its status is `AWAITING_INDEPENDENT_SIGNOFF`: the validator
checks structure/hash and cannot attest that a human or third party really did
the work. The QA owner must authenticate the evidence and grant a separate
staging/production GO. Any missing P0 scope or unsafe payment/restore = **NO-GO**.

### WCAG 2.2 AA human observation matrix (initial scope, not an automatic PASS)

For each row capture outcome `PASS/FAIL/PARTIAL/NOT_RUN`, page/state, device,
manual steps, actual result, reviewer, timestamp and private evidence reference.
This is a targeted sample plan; review **all applicable WCAG 2.2 AA success
criteria** before a conformance claim, including failures not listed here.

| SC | Human check | Representative state |
| --- | --- | --- |
| 1.1.1 | Image alt/meaning and decorative handling | image block / shop product |
| 1.3.1 / 1.3.2 | Heading, landmark, list/table semantics and reading order | page, post, search, nav |
| 1.4.3 / 1.4.11 | Text and UI-state contrast | links, focus, buttons, checkout errors |
| 1.4.4 / 1.4.10 / 1.4.12 | Text scaling, 320px reflow, spacing override | long title, table, checkout |
| 2.1.1 / 2.1.2 | All functions usable by keyboard without traps | navigation open/close, forms |
| 2.2.2 | Pause/stop for any moving content (if present) | whole sample |
| 2.4.1 / 2.4.3 / 2.4.7 / 2.4.11 | Bypass, tab order, focus visibility and non-obscured focus | nav, Gutenberg, checkout |
| 2.5.3 / 2.5.8 | Label in name and target size | mobile controls, buttons |
| 3.2.1 / 3.2.2 | Predictable focus/input behavior | search, checkout |
| 3.3.1 / 3.3.2 / 3.3.3 | Form errors, labels and suggestions | WooCommerce invalid checkout |
| 3.3.8 | Accessible authentication | WordPress login (where applicable) |
| 4.1.2 / 4.1.3 | Accessible names/roles/values and status messages | overlay, validation, cart |

Record WCAG-EM sample selection rationale, excluded features, browsers,
assistive technologies, inconclusive automated rules, defects and retest links.
Do not equate a clean axe scan with completion of this matrix.

### Evidence separation for the technical gap checks (15 October 2026)

- The CI Gutenberg fixtures use real browser-loaded Core editor data stores, but
  **not** the human UI commands for inserting blocks, recovering an invalid
  block, setting image alt text, or editing a header/footer in Site Editor.
  On staging, perform each action with pointer and keyboard and record separate
  UI outcome + persisted post/part IDs (no credentials in public logs).
- Header/footer REST override + delete tests in disposable WordPress show
  persistence/reversion but do **not** demonstrate that Site Editor Save,
  navigation-menu UI or Global Styles visual controls work for real editors.
  Record these separately with administrator and editor permissions.
- The automated Escape-key focus check is not a human screen-reader result.
  Record one keyboard-only task log and NVDA/Firefox plus VoiceOver/Safari
  navigation and checkout task logs using WCAG-EM 2.0; include unresolved
  axe-core incomplete rules in the evaluator's inspection list.
- The disposable theme switch and Docker backup do not replace hosting-specific
  backup/restore, caching, URL/HTTPS behavior, or external test-mode payments.
  These retain `NOT_RUN`/`BLOCKED` until a specific authorized staging URL,
  reviewer and private evidence IDs exist.
