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


def main():
    assert AXE.is_file(), f'The pinned axe-core file is missing: {AXE}'
    paths = ['/', '/starter-page/', '/example-ci-post/', '/?s=Example', '/ci-nonexistent-page-938722/']
    summaries = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={'width': 390, 'height': 844})
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
            }, indent=2) + '\n')
            issues = sum(len(x['violations']) for x in summaries)
            print(f'AXE ADVISORY: scanned {len(summaries)} routes; {issues} violations reported; human WCAG-EM still required')
        finally:
            browser.close()


if __name__ == '__main__':
    main()
