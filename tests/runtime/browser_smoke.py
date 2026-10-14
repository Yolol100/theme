"""Non-destructive browser integration tests against a disposable WordPress CI site.

A route check is not a substitute for Gutenberg save/reload, WCAG-EM, or payments.
"""
import os
from playwright.sync_api import sync_playwright

BASE = os.environ.get('BASE_URL', 'http://localhost:8080').rstrip('/')
WOO = os.environ.get('ENABLE_WOO', '0') == '1'


def verify(page, path, status=200, includes=()):
    response = page.goto(BASE + path, wait_until='domcontentloaded', timeout=45000)
    assert response is not None and response.status == status, (
        f'{path}: HTTP {None if response is None else response.status}, expected {status}'
    )
    assert page.locator('main').count() == 1, f'{path}: expected exactly one main landmark'
    text = page.locator('body').inner_text().strip()
    assert text and page.title().strip(), f'{path}: empty document or missing title'
    for expected in includes:
        assert expected in text, f'{path}: missing fixture text {expected!r}'
    assert page.locator('link[rel="canonical"]').count() <= 1, f'{path}: duplicate canonicals'
    assert 'There has been a critical error' not in text


def main():
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.on('pageerror', lambda error: errors.append(str(error)))
            verify(page, '/', includes=('Latest posts', 'CI Archive Article'))
            verify(page, '/starter-page/', includes=('Starter Page', 'A visible example page'))
            verify(page, '/example-ci-post/', includes=('Example CI Post', 'Testing the Webactueel Starter'))
            verify(page, '/?s=Example', includes=('Example CI Post',))
            verify(page, '/?s=ci-nothing-0d9e7b4', includes=('No posts found',))
            verify(page, '/category/ci-category/', includes=('Example CI Post',))
            verify(page, '/?paged=3', includes=('Example CI Post',))
            verify(page, '/ci-nonexistent-page-938722/', status=404, includes=('Page not found',))
            search = page.locator('main input[type="search"]').first
            search.fill('Example')
            search.press('Enter')
            page.wait_for_url('**/?s=Example', timeout=15000)
            assert 'Example CI Post' in page.locator('main').inner_text()
            response = page.goto(BASE + '/wp-sitemap.xml')
            assert response and response.status == 200, 'WordPress native sitemap missing'
            if WOO:
                for path in ('/shop/', '/cart/', '/checkout/', '/product/ci-test-product/'):
                    verify(page, path)
                verify(page, '/product/ci-test-product/', includes=('CI Test Product',))
            # Check the full content fixture, not only the empty-ish homepage.
            # A table may scroll internally; the document itself must never grow.
            paths = ('/', '/starter-page/', '/example-ci-post/', '/ci-long-content/')
            if WOO:
                paths += ('/shop/', '/cart/', '/checkout/', '/product/ci-test-product/')
            for width in (320, 375, 390, 768, 1024, 1440, 1920):
                page.set_viewport_size({'width': width, 'height': 850})
                for path in paths:
                    verify(page, path)
                    dimensions = page.evaluate("""() => ({
                        viewport: window.innerWidth,
                        document: document.documentElement.scrollWidth
                    })""")
                    assert dimensions['document'] <= dimensions['viewport'] + 2, (
                        f'Horizontal document overflow: {width}px {path} {dimensions}'
                    )
                    if path == '/ci-long-content/':
                        # Computed CSS proves the theme.json rule is active on
                        # the rendered frontend, rather than only in a file.
                        styles = page.evaluate("""() => {
                            const title = document.querySelector('.wp-block-post-title');
                            const content = document.querySelector('.wp-block-post-content');
                            const table = content?.querySelector('.wp-block-table');
                            return title && content && table ? {
                                title: getComputedStyle(title).overflowWrap,
                                content: getComputedStyle(content).overflowWrap,
                                tableOverflow: getComputedStyle(table).overflowX
                            } : null;
                        }""")
                        assert styles == {
                            'title': 'anywhere', 'content': 'anywhere', 'tableOverflow': 'auto'
                        }, f'Missing frontend theme.json reflow CSS: {width}px {styles}'
                        assert 'UnbrokenTitle' in page.locator('h1').inner_text()
                        assert 'UnbrokenHeading' in page.locator('.wp-block-post-content h2').inner_text()
                        assert 'UnbrokenWord' in page.locator('.wp-block-post-content').inner_text()
            assert not errors, f'Uncaught browser JavaScript errors: {errors}'
            print('PASS: routes, 7 viewport widths, rendered theme.json CSS, long content and WooCommerce reflow (when enabled)')
        finally:
            browser.close()


if __name__ == '__main__':
    main()
