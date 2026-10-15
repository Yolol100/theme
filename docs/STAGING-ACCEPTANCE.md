# Independent staging acceptance: NO automatic production GO

CI exercises **disposable** WordPress, offline cheque checkout and temporary database/uploads restore. It cannot certify a live host, WCAG, external payments or client-specific plugins. The 77 scenarios in `77-scenarios.json` remain separate; none is passed without a matching evidence receipt.

## Six mandatory gates

1. **`gutenberg_ui`** — using real UI: administrator/editor separately create, edit, publish, reopen page/post; test header, footer, navigation, Global Styles, media/alt, tables, invalid blocks, permissions and theme switching. Compare saved frontend. WP-CLI/REST/store operations are not equivalent.
2. **`responsive_devices`** — check widths 320, 375, 390, 768, 1024, 1440, 1920px; long words, headings, tables, images, overlays and real zoom to 200%; record device/browser failures.
3. **`wcag_em`** — use **WCAG-EM 2.0 / WCAG 2.2 AA**, select representative pages/states including menus, search, invalid forms and checkout. Human keyboard, focus, contrast, reflow, NVDA/Firefox and VoiceOver/Safari where applicable. Axe is supporting evidence, not certification.
4. **`payment_sandbox`** — on authorized staging only, disable live keys and transactions, use the installed payment provider's official test mode. Verify accepted/declined (and applicable auth) payments, order/stock status, errors, callbacks and refunds. Offline cheque tests are NOT a payment sandbox.
5. **`hosting_rollback`** — with owner approval, verify backup of database, files/uploads and environment. Perform an authorized **real host staging** restore, then check admin, content, assets, URLs/HTTPS, cache, checkout/session flows. Never run destructive restoration in production without separate authorization.
6. **`owner_signoff`** — independent reviewer confirms authentic evidence and zero unresolved critical/high/medium findings for launch scope; no automatic approval.

## Record and validate

In a **private** receipt record: current full commit SHA, exact ZIP SHA-256, staging HTTPS URL, WP/PHP/plugin/host versions, reviewer and timestamp, page/action, expected/actual results, screenshots/log references and PASS/FAIL/PARTIAL/NOT_RUN/BLOCKED/justified N/A. Protect client data and credentials.

```bash
python3 scripts/validate_staging_acceptance.py private-receipt.json   --zip dist/Webactueel-Block-Starter-1.0.5-STAGING.zip   --expected-commit <full-commit-sha> --require-complete
```

Start from `staging-acceptance.example.json` (deliberately `NO_GO`). Even a structurally valid complete receipt returns **`AWAITING_INDEPENDENT_SIGNOFF`**: only an authorized owner and QA can grant a real staging/production GO. Do not lower requirements because a test is costly or unavailable.

Sources: [W3C WCAG-EM](https://www.w3.org/WAI/test-evaluate/conformance/wcag-em/) · [WooCommerce checkout theming](https://developer.woocommerce.com/docs/theming/block-theme-development/cart-and-checkout).
