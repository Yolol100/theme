"""Automated WCAG-related findings on synthetic disposable CI pages.

This creates advisory evidence only: axe cannot certify WCAG AA or test an
actual screen reader. Keep manual/human findings separate in staging review.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get('BASE_URL', 'http://localhost:8080').rstrip('/')
AXE = Path(os.environ.get('AXE_JS_PATH', 'node_modules/axe-core/axe.min.js'))
REPORT = Path('reports/axe-audit.json')


def keyboard_and_mobile_checks(page):
    page.set_viewport_size({'width':375,'height':812})
    response=page.goto(BASE+'/',wait_until='domcontentloaded')
    assert response and response.status==200
    trigger=page.locator('.wp-block-navigation__responsive-container-open').first
    assert trigger.is_visible(), 'Missing mobile navigation button'
    trigger.focus()
    page.keyboard.press('Enter')
    page.locator('.wp-block-navigation__responsive-container.is-menu-open').wait_for(state='visible',timeout=12000)
    page.locator('.wp-block-navigation__responsive-container-close').first.focus()
    page.keyboard.press('Enter')
    page.wait_for_function("() => !document.querySelector('.wp-block-navigation__responsive-container.is-menu-open')",timeout=12000)
    for width in (320,375,390,768,1280):
        page.set_viewport_size({'width':width,'height':850})
        for path in ('/','/ci-long-content/'):
            response=page.goto(BASE+path,wait_until='domcontentloaded')
            assert response and response.status==200
            dimensions=page.evaluate("() => ({w:innerWidth,s:document.documentElement.scrollWidth})")
            assert dimensions['s']<=dimensions['w']+2, (width,path,dimensions)
    return {'mobile_keyboard':'PASS','long_content_reflow':'PASS','screenreader':'NOT_RUN'}


def main():
    assert AXE.is_file(), f'The pinned axe-core file is missing: {AXE}'
    paths = ['/', '/starter-page/', '/example-ci-post/', '/?s=Example', '/ci-nonexistent-page-938722/', '/ci-long-content/']
    summaries = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            interactions=keyboard_and_mobile_checks(page)
            for path in paths:
                response = page.goto(BASE + path, wait_until='domcontentloaded', timeout=45000)
                assert response and response.status in (200, 404)
                page.add_script_tag(path=str(AXE.resolve()))
                result = page.evaluate('''async () => await axe.run(document, {
                  runOnly: { type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa'] }
                })''')
                violations = [
                    {'id': v['id'], 'impact': v['impact'], 'affected_nodes': len(v.get('nodes', []))}
                    for v in result.get('violations', [])
                ]
                summaries.append({'path': path, 'violations': violations,
                                  'incomplete_count': len(result.get('incomplete', [])),
                                  'passes_count': len(result.get('passes', []))})
            REPORT.parent.mkdir(parents=True, exist_ok=True)
            REPORT.write_text(json.dumps({
                'scope': 'advisory-automated-only',
                'human_screenreader_testing': 'NOT_RUN',
                'wcag_conformance_claim': False,
                'pages': summaries,
                'keyboard_and_reflow': interactions,
            }, indent=2) + '\n')
            issues = sum(len(x['violations']) for x in summaries)
            print(f'AXE ADVISORY: scanned {len(summaries)} routes; {issues} violations reported; human WCAG-EM still required')
            assert not any(row['violations'] for row in summaries), 'WCAG automated rule failure on theme pages'
        finally:
            browser.close()


if __name__ == '__main__':
    main()
