"""Read-only browser smoke tests for a disposable WordPress CI instance.

Requires: pip install playwright==1.56.0; python -m playwright install chromium.
This does not claim full WCAG, editor/save, payment or production readiness.
"""
import os
from playwright.sync_api import sync_playwright

BASE = os.environ.get('BASE_URL', 'http://127.0.0.1:8080').rstrip('/')
WOO = os.environ.get('ENABLE_WOO', '0') == '1'


def verify(page, path, status=200):
    response = page.goto(BASE + path, wait_until='domcontentloaded', timeout=45000)
    assert response is not None, f'No response for {path}'
    assert response.status == status, f'{path}: HTTP {response.status}'
    assert page.locator('main').count() == 1, f'{path}: expected one main landmark'
    assert page.locator('body').inner_text().strip(), f'{path}: blank page'


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.on('pageerror', lambda error: errors.append(str(error)))
            for path in ('/', '/starter-page/', '/example-ci-post/', '/?s=Example'):
                verify(page, path)
            verify(page, '/ci-nonexistent-page-938722/', status=404)
            if WOO:
                for path in ('/shop/', '/cart/', '/checkout/', '/product/ci-test-product/'):
                    verify(page, path)
            for width in (320, 375, 390, 768, 1024, 1440, 1920):
                page.set_viewport_size({'width': width, 'height': 850})
                verify(page, '/')
                overflow = page.evaluate(
                    'document.documentElement.scrollWidth > window.innerWidth + 2'
                )
                assert not overflow, f'Horizontal overflow at width {width}'
            assert not errors, f'Uncaught browser JS errors: {errors}'
            print('PASS: frontend routes, 404, viewport reflow and browser errors')
        finally:
            browser.close()


if __name__ == '__main__':
    main()
