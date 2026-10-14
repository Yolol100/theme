"""Automated accessibility evidence on disposable WordPress CI pages.

This is NOT human WCAG-EM assessment, browser zoom testing, or a screen-reader
certificate. Fail on automated WCAG violations in the original theme fixtures;
retain additional WooCommerce findings without declaring third-party code fixed.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get('BASE_URL', 'http://localhost:8080').rstrip('/')
AXE = Path(os.environ.get('AXE_JS_PATH', 'node_modules/axe-core/axe.min.js'))
REPORT = Path('reports/axe-audit.json')
THEME_ROUTES = (
    '/', '/starter-page/', '/example-ci-post/', '/?s=Example',
    '/ci-nonexistent-page-938722/', '/ci-long-content/',
)
WOO_ROUTES = ('/shop/', '/cart/', '/checkout/', '/product/ci-test-product/')
VIEWPORTS = (320, 375, 390, 768, 1024, 1440, 1920)


def axe_scan(page, path, scope, state='default'):
    page.add_script_tag(path=str(AXE.resolve()))
    result = page.evaluate('''async () => await axe.run(document, {
      runOnly: { type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa'] }
    })''')
    return {
        'path': path, 'scope': scope, 'state': state,
        'violations': [
            {'id': v['id'], 'impact': v['impact'],
             'affected_nodes': len(v.get('nodes', [])),
             'targets': [n.get('target') for n in v.get('nodes', [])][:5],
             'html': [n.get('html', '')[:350] for n in v.get('nodes', [])][:3]}
            for v in result.get('violations', [])
        ],
        'incomplete_count': len(result.get('incomplete', [])),
        'incomplete_rules': [
            {'id': r['id'], 'targets': [n.get('target') for n in r.get('nodes', [])][:5]}
            for r in result.get('incomplete', [])
        ],
        'passes_count': len(result.get('passes', [])),
    }


def keyboard_and_mobile_checks(page):
    page.set_viewport_size({'width': 375, 'height': 812})
    response = page.goto(BASE + '/', wait_until='domcontentloaded')
    assert response and response.status == 200
    trigger = page.locator('.wp-block-navigation__responsive-container-open').first
    assert trigger.is_visible(), 'Missing mobile navigation button'
    trigger.focus()
    assert trigger.evaluate('(node) => document.activeElement === node'), 'Navigation trigger not keyboard-focusable'
    # Track focus appearance for the human review; CSS is not a full focus test.
    focus = trigger.evaluate('''(node) => ({
        outlineStyle: getComputedStyle(node).outlineStyle,
        outlineWidth: getComputedStyle(node).outlineWidth,
        label: node.getAttribute('aria-label') || node.textContent.trim()
    })''')
    assert focus['label'], 'Mobile menu trigger needs an accessible name'
    page.keyboard.press('Enter')
    menu = page.locator('.wp-block-navigation__responsive-container.is-menu-open')
    menu.wait_for(state='visible', timeout=12000)
    assert page.locator('.wp-block-navigation__responsive-container-close').first.is_visible()
    open_menu = axe_scan(page, '/', 'theme', 'mobile-menu-open')
    # Close with keyboard only and verify focus returns to the opener.
    page.keyboard.press('Escape')
    page.wait_for_function(
        "() => !document.querySelector('.wp-block-navigation__responsive-container.is-menu-open')",
        timeout=12000,
    )
    focus_returned=trigger.evaluate('(node) => document.activeElement === node')
    assert focus_returned, 'Mobile menu Escape did not return focus to its trigger'
    # Confirm a subsequent keyboard activation still works and the close
    # button can close without pointer input.
    page.keyboard.press('Enter')
    menu.wait_for(state='visible', timeout=12000)
    page.locator('.wp-block-navigation__responsive-container-close').first.focus()
    page.keyboard.press('Enter')
    page.wait_for_function(
        "() => !document.querySelector('.wp-block-navigation__responsive-container.is-menu-open')",
        timeout=12000,
    )
    dimensions = []
    for width in VIEWPORTS:
        page.set_viewport_size({'width': width, 'height': 850})
        for path in ('/', '/ci-long-content/'):
            response = page.goto(BASE + path, wait_until='domcontentloaded')
            assert response and response.status == 200
            size = page.evaluate('''() => ({
                viewport: innerWidth, document: document.documentElement.scrollWidth
            })''')
            assert size['document'] <= size['viewport'] + 2, (width, path, size)
            dimensions.append({'width': width, 'path': path, 'scroll_width': size['document']})
            if width == 320 and path == '/ci-long-content/':
                screenshot = Path('reports/screenshots/long-content-320.png')
                screenshot.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot), full_page=True)
    return {
        'mobile_keyboard': 'PASS', 'focus_return_after_escape': 'PASS',
        'long_content_reflow': 'PASS',
        'focus_inspection': focus, 'measurements': dimensions,
        'screenreader': 'NOT_RUN', 'real_browser_zoom': 'NOT_RUN',
    }, open_menu


def main():
    assert AXE.is_file(), f'The pinned axe-core file is missing: {AXE}'
    summary = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            interactions, opened = keyboard_and_mobile_checks(page)
            summary.append(opened)
            for path in THEME_ROUTES:
                response = page.goto(BASE + path, wait_until='domcontentloaded', timeout=45000)
                assert response and response.status in (200, 404)
                summary.append(axe_scan(page, path, 'theme'))
            if os.environ.get('ENABLE_WOO', '0') == '1':
                for path in WOO_ROUTES:
                    response = page.goto(BASE + path, wait_until='domcontentloaded', timeout=45000)
                    assert response and response.status == 200, f'WooCommerce route failed: {path}'
                    summary.append(axe_scan(page, path, 'woocommerce-integration'))
            REPORT.parent.mkdir(parents=True, exist_ok=True)
            REPORT.write_text(json.dumps({
                'scope': 'advisory-automated-only',
                'methodology': 'axe-core WCAG tagged checks; NOT WCAG-EM 2.0',
                'human_screenreader_testing': 'NOT_RUN',
                'wcag_conformance_claim': False,
                'pages': summary,
                'keyboard_and_reflow': interactions,
                'woocommerce_integration_review_required': any(
                    p['violations'] for p in summary if p['scope'] == 'woocommerce-integration'
                ),
            }, indent=2) + '\n')
            theme_findings = [
                (row['path'], row['state'], row['violations'])
                for row in summary if row['scope'] == 'theme' and row['violations']
            ]
            total = sum(len(row['violations']) for row in summary)
            print(f'AXE ADVISORY: scanned {len(summary)} states; {total} violations reported; human WCAG-EM still required')
            # Never weaken the original CI gate to make an accessibility finding disappear.
            assert not any(row['violations'] for row in summary if row['scope'] == 'theme'), (
                f'WCAG automated rule failure on theme pages: {theme_findings}'
            )
        finally:
            browser.close()


if __name__ == '__main__':
    main()
